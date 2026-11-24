"""Shared timeline for the full-3D cut: scene boundaries fitted to the neural voiceover."""
OLD = [0, 4, 9, 14, 18.5, 23, 26, 30]
NEW = [0, 4.6, 10.2, 14.8, 18.7, 23.1, 26.4, 30]
def remap(t):
    for i in range(len(OLD) - 1):
        if t <= OLD[i + 1] or i == len(OLD) - 2:
            a, b, c, d = OLD[i], OLD[i + 1], NEW[i], NEW[i + 1]
            return c + (t - a) * (d - c) / (b - a)
