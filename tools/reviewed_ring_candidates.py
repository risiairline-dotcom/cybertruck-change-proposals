"""Reviewed original functions for offline reproduction only; retain known defects."""

# Reviewed attachment v1; SHA256: c7d93b4b80e7b371cd312f798f8f2a81477a19d17ed849923d4ef94834379d24
import cv2, numpy as np

def refine_ring_v1(gray, cx, cy, r0, dr=20, n_ang=720):
    """r0: 粗估半径; 返回 (cx, cy, R) 亚像素中心"""
    r_max = int(r0 + dr)
    polar = cv2.warpPolar(gray, (r_max, n_ang), (float(cx), float(cy)),
                          float(r_max), cv2.WARP_POLAR_LINEAR)
    prof = cv2.GaussianBlur(polar.astype(np.float32), (5, 1), 0)   # 只沿半径平滑
    g = np.abs(np.diff(prof, axis=1))                              # 行=角度, 列=半径
    lo, hi = max(1, int(r0 - dr)), min(g.shape[1] - 2, int(r0 + dr))
    k = np.argmax(g[:, lo:hi], axis=1) + lo
    a = g[np.arange(n_ang), k - 1]; b = g[np.arange(n_ang), k]; c = g[np.arange(n_ang), k + 1]
    den = a - 2 * b + c
    sub = k + np.where(np.abs(den) > 1e-6, 0.5 * (a - c) / den, 0.0)  # 抛物线亚像素
    th = np.linspace(0, 2 * np.pi, n_ang, endpoint=False)
    A = np.column_stack([np.ones(n_ang), np.cos(th), np.sin(th)])    # r(θ)=R+dx·cosθ+dy·sinθ
    coef, *_ = np.linalg.lstsq(A, sub, rcond=None)
    return cx + coef[1], cy + coef[2], coef[0]

# Reviewed attachment v2; SHA256: fcc00821e48fe42c559b08fcb7667a027d4c8114993ac43da2ed70b651e3a0a7
import cv2, numpy as np

def refine_ring_v2(gray, cx, cy, r0, dr, n_ang=720,
                min_cov=0.55, max_rms=0.8, dark=18.0):
    """r0/dr 来自粗检测的单层半径；返回 (x,y,R) 或 None。"""
    r_max = int(r0 + dr) + 2
    polar = cv2.warpPolar(gray.astype(np.float32), (r_max, n_ang), (float(cx), float(cy)),
                          float(r_max), cv2.WARP_POLAR_LINEAR | cv2.INTER_LINEAR)
    prof = cv2.GaussianBlur(polar, (1, 3), 0)          # 只沿半径方向平滑
    lo, hi = max(1, int(r0 - dr)), min(prof.shape[1] - 2, int(r0 + dr))
    band = prof[:, lo:hi]; rows = np.arange(n_ang)
    k = np.argmin(band, axis=1); val = band[rows, k]    # 环线中心 = 强度极小
    idx = np.clip(k, 1, band.shape[1] - 2)
    a, b, c = band[rows, idx-1], band[rows, idx], band[rows, idx+1]
    den = a - 2*b + c
    with np.errstate(divide='ignore', invalid='ignore'):
        sub = idx + np.where(np.abs(den) > 1e-6, 0.5*(a-c)/den, 0.0) + lo
    bg = float(np.median(band))
    ok = (b < a) & (b <= c) & (val <= bg - dark) & (sub > r0-dr) & (sub < r0+dr)
    cov = float(ok.mean())
    if cov < min_cov:
        return None                                     # 覆盖率不足：弃判，不硬给中心
    th = np.linspace(0, 2*np.pi, n_ang, endpoint=False)[ok]; r = sub[ok]
    A = np.column_stack([np.ones_like(th), np.cos(th), np.sin(th),
                         np.cos(2*th), np.sin(2*th)])    # 2θ 吸收椭圆/轻微透视
    coef, *_ = np.linalg.lstsq(A, r, rcond=None)
    rms = float(np.sqrt(np.mean((r - A @ coef)**2)))
    if rms > max_rms:
        return None                                     # 残差超标：层串了或不是环
    return cx + coef[1], cy + coef[2], float(coef[0])
