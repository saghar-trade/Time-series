import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --------------------------
# تنظیمات
# --------------------------
LEFT = 3
RIGHT = 3
DISPLACEMENT_BODY_RATIO = 1.5
FVG_WINDOW = 2
SCORE_THRESHOLD = 4

# --------------------------
# داده نمونه (اگر فایل CSV داری این خط را تغییر بده)
# CSV باید ستون‌های: time, open, high, low, close داشته باشه
# --------------------------
# df = pd.read_csv("candles.csv")
dates = pd.date_range("2023-01-01", periods=50, freq="H")
np.random.seed(0)
prices = np.cumsum(np.random.randn(50)) + 100
df = pd.DataFrame({
    "time": dates,
    "open": prices,
    "high": prices + np.random.rand(50)*2,
    "low": prices - np.random.rand(50)*2,
    "close": prices + np.random.randn(50)*0.5,
})

# --------------------------
# تشخیص سوینگ‌ها
# --------------------------
def detect_swings(data, left=3, right=3):
    swings = []
    for i in range(left, len(data)-right):
        is_high = all(data["high"].iloc[i] > data["high"].iloc[i-j] for j in range(1,left+1)) and \
                  all(data["high"].iloc[i] > data["high"].iloc[i+j] for j in range(1,right+1))
        is_low = all(data["low"].iloc[i] < data["low"].iloc[i-j] for j in range(1,left+1)) and \
                 all(data["low"].iloc[i] < data["low"].iloc[i+j] for j in range(1,right+1))
        if is_high:
            swings.append((i, "H"))
        if is_low:
            swings.append((i, "L"))
    return swings

swings = detect_swings(df, LEFT, RIGHT)

# --------------------------
# پیدا کردن BOS
# --------------------------
bos = []
for i in range(1, len(swings)):
    prev_idx, prev_type = swings[i-1]
    idx, typ = swings[i]
    if typ == "H" and df["high"].iloc[idx] > df["high"].iloc[prev_idx]:
        bos.append((idx, "BOS_up"))
    if typ == "L" and df["low"].iloc[idx] < df["low"].iloc[prev_idx]:
        bos.append((idx, "BOS_down"))

# --------------------------
# پیدا کردن Order Block (OB)
# --------------------------
ob_zones = []
for idx, typ in bos:
    if typ == "BOS_up":
        # آخرین کندل نزولی قبل از BOS
        lookback = df.iloc[max(0, idx-5):idx]
        bearish = lookback[lookback["close"] < lookback["open"]]
        if not bearish.empty:
            ob = bearish.iloc[-1]
            ob_zones.append(("bullish", ob["low"], ob["high"], idx))
    elif typ == "BOS_down":
        # آخرین کندل صعودی قبل از BOS
        lookback = df.iloc[max(0, idx-5):idx]
        bullish = lookback[lookback["close"] > lookback["open"]]
        if not bullish.empty:
            ob = bullish.iloc[-1]
            ob_zones.append(("bearish", ob["low"], ob["high"], idx))

# --------------------------
# محاسبه امتیاز زون‌ها
# --------------------------
zones = []
for direction, low, high, bos_idx in ob_zones:
    score = 0
    # اگر displacement زیاد باشد
    rng = df.iloc[bos_idx-3:bos_idx+1]
    if len(rng)>0:
        body = abs(rng["close"].iloc[-1]-rng["open"].iloc[0])
        wick = (rng["high"].max()-rng["low"].min())
        if body > DISPLACEMENT_BODY_RATIO * wick/2:
            score += 2
    # اگر زون چند بار تست شده
    touches = ((df["low"] <= high) & (df["high"] >= low)).sum()
    score += min(2, touches)
    if score >= SCORE_THRESHOLD:
        zones.append((direction, low, high, score, bos_idx))

# --------------------------
# نمایش
# --------------------------
fig, ax = plt.subplots(figsize=(12,6))
ax.plot(df["time"], df["close"], label="Close Price")
for direction, low, high, score, idx in zones:
    ax.axhspan(low, high, color="green" if direction=="bullish" else "red", alpha=0.3)
    ax.text(df["time"].iloc[idx], (low+high)/2, f"{direction}\nscore:{score}")
plt.legend()
plt.show()

