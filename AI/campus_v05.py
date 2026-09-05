"""CPU vegetation segmentation experiment; assisted labels are not ground truth."""
import argparse
import csv
import hashlib
import json
import random
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

try:
    from AI.vegetation_baseline import vegetation_mask
except ImportError:
    from vegetation_baseline import vegetation_mask

RUN = Path(__file__).resolve().parent / 'runs' / 'campus_v05'


class VegetationNet(nn.Module):
    def __init__(self):
        super().__init__()
        def block(a, b):
            return nn.Sequential(nn.Conv2d(a, b, 3, padding=1), nn.ReLU(),
                                 nn.Conv2d(b, b, 3, padding=1), nn.ReLU())
        self.enc1 = block(3, 16)
        self.enc2 = block(16, 32)
        self.center = block(32, 64)
        self.dec2 = block(96, 32)
        self.dec1 = block(48, 16)
        self.out = nn.Conv2d(16, 1, 1)

    def forward(self, x):
        a = self.enc1(x)
        b = self.enc2(F.max_pool2d(a, 2))
        c = self.center(F.max_pool2d(b, 2))
        d = self.dec2(torch.cat([F.interpolate(c, size=b.shape[2:], mode='bilinear', align_corners=False), b], 1))
        return self.out(self.dec1(torch.cat([F.interpolate(d, size=a.shape[2:], mode='bilinear', align_corners=False), a], 1)))


def read_image(path, flags):
    image = cv2.imdecode(np.fromfile(path, dtype=np.uint8), flags)
    if image is None:
        raise ValueError(f'Cannot decode {path}')
    return image


def tensor_image(image, size):
    resized = cv2.resize(image, (size, size))
    return torch.from_numpy(cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).transpose(2, 0, 1).copy()).float() / 255


def load_model(path=RUN / 'best.pt'):
    checkpoint = torch.load(path, map_location='cpu', weights_only=True)
    net = VegetationNet()
    net.load_state_dict(checkpoint['state_dict'])
    net.eval()
    return net, checkpoint['size']


@torch.inference_mode()
def predict_mask(net, image, size):
    probability = net(tensor_image(image, size)[None]).sigmoid()[0, 0].numpy()
    return cv2.resize(probability, (image.shape[1], image.shape[0])) >= 0.5


def score(prediction, target, valid):
    return np.array([np.count_nonzero(prediction & target & valid),
                     np.count_nonzero(prediction & ~target & valid),
                     np.count_nonzero(~prediction & target & valid)], dtype=np.int64)


def metrics(counts, errors):
    tp, fp, fn = map(int, counts)
    return {'iou': tp / max(tp + fp + fn, 1), 'dice': 2 * tp / max(2 * tp + fp + fn, 1),
            'precision': tp / max(tp + fp, 1), 'recall': tp / max(tp + fn, 1),
            'coverage_mae_percentage_points': float(np.mean(errors)), 'tp': tp, 'fp': fp, 'fn': fn}


def evaluate(net, records, size, output=None):
    counts = {'network': np.zeros(3, np.int64), 'exg': np.zeros(3, np.int64)}
    errors = {key: [] for key in counts}
    if output:
        output.mkdir(parents=True, exist_ok=True)
    for row, image, mask in records:
        valid, target = mask != 255, np.isin(mask, [1, 2, 3])
        prediction = predict_mask(net, image, size)
        baseline = vegetation_mask(image)[0] > 0
        for key, pred in [('network', prediction), ('exg', baseline)]:
            counts[key] += score(pred, target, valid)
            errors[key].append(100 * abs(float(pred[valid].mean()) - float(target[valid].mean())))
        if output:
            panels = [image]
            for region in [target, prediction, baseline]:
                overlay = image.copy()
                overlay[region] = (0.5 * overlay[region] + np.array([0, 127, 0])).astype(np.uint8)
                panels.append(overlay)
            board = np.concatenate([cv2.resize(p, (320, 240)) for p in panels], axis=1)
            cv2.imencode('.jpg', board)[1].tofile(output / f"{row['id']}.jpg")
    return {key: metrics(counts[key], errors[key]) for key in counts}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--epochs', type=int, default=40)
    parser.add_argument('--size', type=int, default=192)
    parser.add_argument('--output', type=Path, default=RUN)
    args = parser.parse_args()
    if (args.output / 'best.pt').exists():
        raise FileExistsError('Use a new --output directory to preserve the prior experiment.')
    torch.set_num_threads(4)
    torch.manual_seed(42)
    np.random.seed(42)
    random.seed(42)
    torch.use_deterministic_algorithms(True)
    rows = json.loads((args.source / 'manifest.json').read_text(encoding='utf-8-sig'))
    splits = {'train_suggested': [], 'validation_to_refine': [], 'challenge_holdout': []}
    groups, hashes = {}, set()
    audit = []
    for row in rows:
        split = row['recommended_split']
        group = row['location_group']
        if group in groups and groups[group] != split:
            raise ValueError(f'Location leakage: {group}')
        groups[group] = split
        for field, digest_field in [('relative_path', 'sha256'), ('mask_path', 'mask_sha256')]:
            digest = hashlib.sha256((args.source / row[field]).read_bytes()).hexdigest()
            if digest != row[digest_field]:
                raise ValueError(f"Hash mismatch: {row['id']} {field}")
        if row['sha256'] in hashes:
            raise ValueError(f"Duplicate image: {row['id']}")
        hashes.add(row['sha256'])
        image = read_image(args.source / row['relative_path'], cv2.IMREAD_COLOR)
        mask = read_image(args.source / row['mask_path'], cv2.IMREAD_GRAYSCALE)
        if mask.shape != image.shape[:2] or not set(np.unique(mask)).issubset(set(range(10)) | {255}):
            raise ValueError(f"Invalid mask: {row['id']}")
        if not np.any(mask != 255):
            raise ValueError(f"No valid pixels: {row['id']}")
        splits[split].append((row, image, mask))
        audit.append({key: row[key] for key in ['id', 'recommended_split', 'location_group', 'sha256', 'mask_sha256', 'source_page', 'license']})
    if any(not records for records in splits.values()):
        raise ValueError('All splits must contain samples')
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'data_audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
    train = []
    for _, image, mask in splits['train_suggested']:
        small = cv2.resize(mask, (args.size, args.size), interpolation=cv2.INTER_NEAREST)
        train.append((tensor_image(image, args.size), torch.from_numpy(np.isin(small, [1, 2, 3]).astype(np.float32))[None], torch.from_numpy(small != 255)[None]))
    net = VegetationNet()
    optimizer = torch.optim.Adam(net.parameters(), lr=0.001)
    best, history = -1.0, []
    for epoch in range(1, args.epochs + 1):
        net.train()
        random.shuffle(train)
        losses = []
        for start in range(0, len(train), 5):
            batch = train[start:start + 5]
            x, y, valid = [torch.stack(items) for items in zip(*batch)]
            if random.random() < 0.5:
                x, y, valid = [t.flip(-1) for t in (x, y, valid)]
            optimizer.zero_grad()
            logits = net(x)
            bce = F.binary_cross_entropy_with_logits(logits, y, reduction='none')[valid].mean()
            p = logits.sigmoid()[valid]
            truth = y[valid]
            loss = bce + 1 - (2 * (p * truth).sum() + 1) / (p.sum() + truth.sum() + 1)
            loss.backward()
            optimizer.step()
            losses.append(loss.item())
        net.eval()
        # Only validation controls checkpoint selection. Holdout is evaluated once below.
        validation = evaluate(net, splits['validation_to_refine'], args.size)
        iou = validation['network']['iou']
        history.append({'epoch': epoch, 'loss': float(np.mean(losses)), 'val_iou': iou})
        if iou > best:
            best = iou
            torch.save({'state_dict': net.state_dict(), 'size': args.size, 'epoch': epoch}, args.output / 'best.pt')
        print(f'Epoch {epoch}/{args.epochs} loss={np.mean(losses):.4f} val_iou={iou:.4f}', flush=True)
    with (args.output / 'history.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=history[0].keys())
        writer.writeheader()
        writer.writerows(history)
    net, size = load_model(args.output / 'best.pt')
    report = {'created_at': datetime.now(timezone.utc).isoformat(), 'source': str(args.source),
              'split_counts': {k: len(v) for k, v in splits.items()}, 'seed': 42, 'epochs': args.epochs,
              'size': size, 'device': 'cpu', 'architecture': 'small U-Net from scratch',
              'target': 'visible vegetation: tree + low_vegetation + grass', 'ignore_index': 255,
              'label_status': 'model-assisted, AI-reviewed; NOT independent human ground truth',
              'best_epoch': torch.load(args.output / 'best.pt', weights_only=True)['epoch'],
              'validation': evaluate(net, splits['validation_to_refine'], size, args.output / 'validation_previews'),
              'holdout': evaluate(net, splits['challenge_holdout'], size, args.output / 'holdout_previews')}
    (args.output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=True, indent=2), flush=True)


if __name__ == '__main__':
    main()
