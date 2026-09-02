# ==========================================================
# NUMERO
# Professional Historical Future Signal Provider
# FULL CODE — QUALIFICATION + RANKING UPGRADED
# ==========================================================

import requests
import json
import os
import time
import sys
import threading
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed


# ==========================================================
# OPTIONAL TQDM
# ==========================================================

try:
    from tqdm import tqdm
except ImportError:

    class tqdm:

        def __init__(self, iterable, desc="", **kwargs):
            self.iterable = iterable
            self.desc = desc

        def __iter__(self):
            for item in self.iterable:
                yield item


# ==========================================================
# COLORS
# ==========================================================

def colored(text, color):

    colors = {
        "green": "\033[92m",
        "red": "\033[91m",
        "cyan": "\033[96m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "bold": "\033[1m",
        "reset": "\033[0m"
    }

    return (
        colors.get(color, "")
        + str(text)
        + colors["reset"]
    )


# ==========================================================
# PROFESSIONAL LOADING ANIMATION (SHORTENED)
# ==========================================================

class ProfessionalLoader:

    def __init__(self, title="NUMERO", total=0):

        self.title = title
        self.total = total

        self.completed = 0
        self.running = False

        self.thread = None

        self.lock = threading.Lock()

        self.frames = [
            "⠋",
            "⠙",
            "⠹",
            "⠸",
            "⠼",
            "⠴",
            "⠦",
            "⠧",
            "⠇",
            "⠏"
        ]

        self.frame_index = 0

        self.start_time = time.time()


    def start(self):

        if self.running:
            return

        self.running = True

        self.start_time = time.time()

        self.thread = threading.Thread(
            target=self._animate,
            daemon=True
        )

        self.thread.start()


    def update(self, completed=None):

        with self.lock:

            if completed is None:
                self.completed += 1
            else:
                self.completed = completed


    def _animate(self):

        while self.running:

            with self.lock:

                completed = self.completed
                total = self.total

                frame = self.frames[
                    self.frame_index
                    % len(self.frames)
                ]

                self.frame_index += 1

            elapsed = time.time() - self.start_time

            if total > 0:

                percent = (
                    completed / total
                ) * 100

                bar_length = 28

                filled = int(
                    bar_length
                    * completed
                    / total
                )

                bar = (
                    "█" * filled
                    + "░" * (
                        bar_length - filled
                    )
                )

                text = (
                    f"\r{colored(frame, 'cyan')} "
                    f"{colored(self.title, 'bold')} "
                    f"[{bar}] "
                    f"{completed}/{total} "
                    f"{percent:6.2f}% "
                    f"Elapsed: {elapsed:5.1f}s"
                )

            else:

                dots = "." * (
                    (self.frame_index % 4)
                )

                text = (
                    f"\r{colored(frame, 'cyan')} "
                    f"{colored(self.title, 'bold')} "
                    f"{dots:<3} "
                    f"Elapsed: {elapsed:5.1f}s"
                )

            sys.stdout.write(text)
            sys.stdout.flush()

            time.sleep(0.05)  # slightly faster


    def stop(self, final_text=None):

        self.running = False

        if self.thread:

            self.thread.join(
                timeout=1
            )

        sys.stdout.write(
            "\r" + (" " * 120) + "\r"
        )

        sys.stdout.flush()

        if final_text:

            print(final_text)


# ==========================================================
# LOADING STAGE ANIMATION (SHORTENED)
# ==========================================================

def loading_stage(text, duration=0.3):  # reduced from 0.6–0.8

    frames = [
        "⠋",
        "⠙",
        "⠹",
        "⠸",
        "⠼",
        "⠴",
        "⠦",
        "⠧",
        "⠇",
        "⠏"
    ]

    start = time.time()

    i = 0

    while time.time() - start < duration:

        frame = frames[
            i % len(frames)
        ]

        sys.stdout.write(
            "\r"
            + colored(
                frame,
                "cyan"
            )
            + " "
            + colored(
                text,
                "cyan"
            )
            + "   "
        )

        sys.stdout.flush()

        i += 1

        time.sleep(0.05)


    sys.stdout.write(
        "\r"
        + colored(
            "✓",
            "green"
        )
        + " "
        + colored(
            text,
            "green"
        )
        + " " * 20
        + "\n"
    )

    sys.stdout.flush()


# ==========================================================
# OANDA CONFIG
# ==========================================================

API_TOKEN = "eb2326208921b413a87728832f191f03-d9be68b74884f7d3107b9f05ca305319"

ACCOUNT_ID = "7993083766"

BASE_URL = "https://api-fxpractice.oanda.com/v3"

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}


# ==========================================================
# SETTINGS
# ==========================================================

TIMEFRAME = "M1"

CACHE_DIR = "zero_future_cache"

MAX_OANDA_CANDLES = 5000

MAX_WORKERS = 5

BAN_PAST_TODAY_SIGNAL = True


# ==========================================================
# SUPPORTED PAIRS
# ==========================================================

PAIRS = [

    "EUR_USD",
    "GBP_USD",
    "USD_JPY",
    "AUD_USD",
    "USD_CAD",
    "USD_CHF",
    "NZD_USD",

    "EUR_JPY",
    "GBP_JPY",
    "EUR_GBP",
    "EUR_CHF",
    "GBP_CHF",

    "AUD_JPY",
    "CAD_JPY",
    "CHF_JPY",

    "XAU_USD"
]


# ==========================================================
# QUALIFICATION FILTERS (STRICT)
# ==========================================================

MIN_SAMPLE_STRICT = 5          # minimum historical samples
MIN_WINRATE_STRICT = 70.0      # minimum winrate (%)
MIN_RECENT_WINRATE = 50.0      # kept for ranking, not for filtering
RECENT_DAYS = 10


# ==========================================================
# CACHE
# ==========================================================

def ensure_cache():

    if not os.path.exists(CACHE_DIR):

        os.makedirs(CACHE_DIR)


def cache_file(pair, start_date, end_date):

    safe_start = start_date.replace(":", "-")
    safe_end = end_date.replace(":", "-")

    return os.path.join(
        CACHE_DIR,
        f"{pair}_{safe_start}_{safe_end}.json"
    )


def load_cache(pair, start_date, end_date):

    path = cache_file(
        pair,
        start_date,
        end_date
    )

    if not os.path.exists(path):

        return None

    try:

        with open(path, "r") as f:

            data = json.load(f)

        if isinstance(data, list):

            return data

    except Exception:

        pass

    return None


def save_cache(
    pair,
    start_date,
    end_date,
    candles
):

    try:

        path = cache_file(
            pair,
            start_date,
            end_date
        )

        with open(path, "w") as f:

            json.dump(
                candles,
                f
            )

    except Exception:

        pass


# ==========================================================
# TIME UTILITIES
# ==========================================================

UTC = timezone.utc

BD_TIMEZONE = timezone(
    timedelta(hours=6)
)


def parse_oanda_time(value):

    try:

        return datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00"
            )
        )

    except Exception:

        return None


def utc_to_bd(dt):

    return dt.astimezone(
        BD_TIMEZONE
    )


def candle_date_bd(candle):

    dt = parse_oanda_time(
        candle["time"]
    )

    if not dt:

        return ""

    return utc_to_bd(dt).strftime(
        "%Y-%m-%d"
    )


def candle_minute_bd(candle):

    dt = parse_oanda_time(
        candle["time"]
    )

    if not dt:

        return -1

    local = utc_to_bd(dt)

    return (
        local.hour * 60
        + local.minute
    )


def minute_to_string(minute):

    return (
        f"{minute // 60:02d}:"
        f"{minute % 60:02d}"
    )


def date_to_datetime(date_string):

    return datetime.strptime(
        date_string,
        "%Y-%m-%d"
    ).replace(
        tzinfo=BD_TIMEZONE
    )


# ==========================================================
# INPUT VALIDATION
# ==========================================================

def valid_time(value):

    try:

        datetime.strptime(
            value,
            "%H:%M"
        )

        return True

    except Exception:

        return False


def time_to_minutes(value):

    parts = value.split(":")

    return (
        int(parts[0]) * 60
        + int(parts[1])
    )


# ==========================================================
# OANDA DOWNLOAD
# ==========================================================

def download_pair_history(
    pair,
    start_dt_utc,
    end_dt_utc
):

    start_iso = (
        start_dt_utc.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    )

    end_iso = (
        end_dt_utc.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    )

    cached = load_cache(
        pair,
        start_iso,
        end_iso
    )

    if cached:

        return pair, cached


    url = (
        f"{BASE_URL}/instruments/"
        f"{pair}/candles"
    )


    all_candles = []

    current_to = end_dt_utc

    max_requests = 100

    requests_done = 0


    while current_to > start_dt_utc:

        if requests_done >= max_requests:

            break


        params = {

            "granularity": TIMEFRAME,

            "price": "M",

            "count": MAX_OANDA_CANDLES,

            "to": current_to.strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
        }


        try:

            response = requests.get(
                url,
                headers=HEADERS,
                params=params,
                timeout=30
            )


            if response.status_code != 200:

                break


            data = response.json()

            raw = data.get(
                "candles",
                []
            )


            if not raw:

                break


            batch = []


            for c in raw:

                if not c.get(
                    "complete",
                    False
                ):

                    continue


                mid = c.get("mid")

                if not mid:

                    continue


                try:

                    batch.append({

                        "time": c["time"],

                        "open": float(
                            mid["o"]
                        ),

                        "high": float(
                            mid["h"]
                        ),

                        "low": float(
                            mid["l"]
                        ),

                        "close": float(
                            mid["c"]
                        )
                    })

                except Exception:

                    continue


            if not batch:

                break


            all_candles.extend(
                batch
            )


            oldest = min(
                batch,
                key=lambda x:
                x["time"]
            )


            oldest_dt = parse_oanda_time(
                oldest["time"]
            )


            if not oldest_dt:

                break


            next_to = (
                oldest_dt
                - timedelta(
                    seconds=1
                )
            )


            if next_to >= current_to:

                break


            current_to = next_to

            requests_done += 1

            time.sleep(0.10)


            if current_to <= start_dt_utc:

                break


        except Exception:

            break


    # ======================================================
    # FILTER RANGE
    # ======================================================

    unique = {}


    for candle in all_candles:

        dt = parse_oanda_time(
            candle["time"]
        )

        if not dt:

            continue


        if (
            dt >= start_dt_utc
            and dt <= end_dt_utc
        ):

            unique[
                candle["time"]
            ] = candle


    candles = list(
        unique.values()
    )


    candles.sort(
        key=lambda x:
        x["time"]
    )


    save_cache(
        pair,
        start_iso,
        end_iso,
        candles
    )


    return pair, candles


# ==========================================================
# LOAD MARKET HISTORY (SHORTENED LOADING)
# ==========================================================

def load_market_history(
    start_dt_utc,
    end_dt_utc
):

    ensure_cache()

    market = {}


    print()

    print(
        colored(
            "╔══════════════════════════════════════════════╗",
            "red"
        )
    )

    print(
        colored(
            "║             N U M E R O                       ║",
            "bold red"
        )
    )

    print(
        colored(
            "╚══════════════════════════════════════════════╝",
            "red"
        )
    )

    print()


    loading_stage(
        "Connecting to OANDA Data Engine",
        0.3
    )

    loading_stage(
        "Preparing M1 candle database",
        0.3
    )

    loading_stage(
        f"Loading {len(PAIRS)} pairs",
        0.3
    )


    print()


    # ======================================================
    # MAIN PROFESSIONAL PROGRESS LOADER
    # ======================================================

    loader = ProfessionalLoader(
        title="DOWNLOADING M1 DATA",
        total=len(PAIRS)
    )

    loader.start()


    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        futures = {

            executor.submit(
                download_pair_history,
                pair,
                start_dt_utc,
                end_dt_utc
            ): pair

            for pair in PAIRS
        }


        completed = 0


        for future in as_completed(
            futures
        ):

            pair = futures[future]


            try:

                result_pair, candles = (
                    future.result()
                )

                market[result_pair] = candles

                completed += 1

                loader.update(
                    completed
                )


            except Exception:

                market[pair] = []

                completed += 1

                loader.update(
                    completed
                )


    loader.stop(
        colored(
            "✓ Historical market data loaded",
            "green"
        )
    )


    # ======================================================
    # DATA SUMMARY
    # ======================================================

    print()

    total_candles = sum(
        len(candles)
        for candles in market.values()
    )


    loader2 = ProfessionalLoader(
        title="VERIFYING DATA INTEGRITY"
    )

    loader2.start()


    time.sleep(0.3)


    loader2.stop(
        colored(
            "✓ Data integrity verified",
            "green"
        )
    )


    print()

    print(
        colored(
            "┌──────────────────────────────────────────────┐",
            "cyan"
        )
    )

    print(
        colored(
            f"│ Pairs Loaded    : {len(market):<26}│",
            "cyan"
        )
    )

    print(
        colored(
            f"│ Total Candles   : {total_candles:<26}│",
            "cyan"
        )
    )

    print(
        colored(
            f"│ Timeframe       : {TIMEFRAME:<26}│",
            "cyan"
        )
    )

    print(
        colored(
            "│ Data Source     : OANDA Historical API       │",
            "cyan"
        )
    )

    print(
        colored(
            "└──────────────────────────────────────────────┘",
            "cyan"
        )
    )

    print()


    return market


# ==========================================================
# BUILD HISTORICAL SETUPS
# ==========================================================

def build_setup_statistics(
    market,
    start_min,
    end_min
):

    setups = defaultdict(list)


    for pair, candles in market.items():

        if len(candles) < 2:

            continue


        for i in range(
            len(candles) - 1
        ):

            current = candles[i]

            next_candle = candles[
                i + 1
            ]


            minute = candle_minute_bd(
                current
            )


            if minute < start_min:

                continue


            if minute > end_min:

                continue


            date = candle_date_bd(
                current
            )


            if not date:

                continue


            next_open = (
                next_candle["open"]
            )

            next_close = (
                next_candle["close"]
            )


            # ==================================================
            # CALL
            # ==================================================

            if next_close > next_open:

                result = 1

            else:

                result = 0


            setups[
                (
                    pair,
                    minute,
                    "CALL"
                )
            ].append({

                "date": date,

                "result": result
            })


            # ==================================================
            # PUT
            # ==================================================

            if next_close < next_open:

                result = 1

            else:

                result = 0


            setups[
                (
                    pair,
                    minute,
                    "PUT"
                )
            ].append({

                "date": date,

                "result": result
            })


    return setups


# ==========================================================
# CALCULATE STATS
# ==========================================================

def calculate_setup_stats(
    setup_data,
    today_date
):

    total = len(
        setup_data
    )


    if total == 0:

        return None


    wins = sum(
        x["result"]
        for x in setup_data
    )


    losses = (
        total - wins
    )


    winrate = (
        wins / total
    ) * 100


    # ======================================================
    # RECENT PERFORMANCE
    # ======================================================

    today_obj = date_to_datetime(
        today_date
    )


    cutoff = (
        today_obj
        - timedelta(
            days=RECENT_DAYS
        )
    )


    recent_results = []


    for item in setup_data:

        try:

            item_date = date_to_datetime(
                item["date"]
            )

            if item_date >= cutoff:

                recent_results.append(
                    item["result"]
                )

        except Exception:

            pass


    if recent_results:

        recent_winrate = (
            sum(recent_results)
            / len(recent_results)
        ) * 100

    else:

        recent_winrate = 0.0


    # ======================================================
    # DAILY CONSISTENCY
    # ======================================================

    daily = defaultdict(list)


    for item in setup_data:

        daily[
            item["date"]
        ].append(
            item["result"]
        )


    daily_rates = []


    for values in daily.values():

        if values:

            daily_rates.append(
                (
                    sum(values)
                    / len(values)
                ) * 100
            )


    if daily_rates:

        average_daily = (
            sum(daily_rates)
            / len(daily_rates)
        )

    else:

        average_daily = 0.0


    # ======================================================
    # SCORE (used only for display, not ranking)
    # ======================================================

    score = (

        winrate * 0.55

        + recent_winrate * 0.25

        + average_daily * 0.20
    )


    return {

        "total": total,

        "wins": wins,

        "losses": losses,

        "winrate": winrate,

        "recent_winrate":
            recent_winrate,

        "average_daily":
            average_daily,

        "score":
            score
    }


# ==========================================================
# CREATE CANDIDATES
# ==========================================================

def create_candidates(
    market,
    start_min,
    end_min,
    today_date
):

    setups = build_setup_statistics(
        market,
        start_min,
        end_min
    )


    candidates = []


    for (
        pair,
        minute,
        direction
    ), data in setups.items():


        stats = calculate_setup_stats(
            data,
            today_date
        )


        if not stats:

            continue


        candidates.append({

            "pair": pair,

            "minute": minute,

            "time":
                minute_to_string(
                    minute
                ),

            "direction":
                direction,

            **stats
        })


    return candidates


# ==========================================================
# RANK CANDIDATES (STRICT QUALIFICATION + RANKING)
# ==========================================================

def rank_candidates(
    candidates,
    required
):

    if not candidates:

        return []


    # ======================================================
    # STRICT QUALIFICATION
    # ======================================================

    qualified = [

        x for x in candidates

        if (

            x["total"]
            >= MIN_SAMPLE_STRICT

            and

            x["winrate"]
            >= MIN_WINRATE_STRICT

            # Recent winrate is not a filter, only ranking
        )
    ]


    # ======================================================
    # RANK: Primary = WinRate, Secondary = Sample Size,
    #        Tertiary = Recent Performance, Consistency
    # ======================================================

    qualified.sort(

        key=lambda x: (

            x["winrate"],

            x["total"],

            x["recent_winrate"],

            x["average_daily"],

            x["wins"]   # tie-breaker

        ),

        reverse=True
    )


    # ======================================================
    # UNIQUE PAIR + TIME (keep the best ranked for each)
    # ======================================================

    unique = []

    used = set()


    for candidate in qualified:

        key = (
            candidate["pair"],
            candidate["minute"]
        )


        if key in used:

            continue


        used.add(key)

        unique.append(
            candidate
        )


    return unique


# ==========================================================
# FUTURE TIME FILTER
# ==========================================================

def filter_future_signals(
    candidates,
    start_min,
    end_min,
    required
):

    now_bd = datetime.now(
        BD_TIMEZONE
    )


    current_minute = (
        now_bd.hour * 60
        + now_bd.minute
    )


    future = []


    for candidate in candidates:

        minute = candidate[
            "minute"
        ]


        if minute < start_min:

            continue


        if minute > end_min:

            continue


        if BAN_PAST_TODAY_SIGNAL:

            if minute <= current_minute:

                continue


        future.append(
            candidate
        )


    # ======================================================
    # Already sorted by rank, so keep order
    # ======================================================

    return future[:required]


# ==========================================================
# GENERATE FUTURE SIGNALS
# ==========================================================

def generate_future_signals(
    market,
    start_min,
    end_min,
    required,
    today_date
):

    print()

    loader = ProfessionalLoader(
        title="ANALYZING HISTORICAL SETUPS"
    )

    loader.start()


    candidates = create_candidates(

        market,

        start_min,

        end_min,

        today_date
    )


    loader.stop(
        colored(
            f"✓ {len(candidates)} historical setups found",
            "green"
        )
    )


    if not candidates:

        return [], 0


    loader2 = ProfessionalLoader(
        title="RANKING QUALIFIED SIGNALS"
    )

    loader2.start()


    ranked = rank_candidates(

        candidates,

        required
    )


    time.sleep(0.2)


    loader2.stop(
        colored(
            f"✓ {len(ranked)} qualified setups ranked",
            "green"
        )
    )


    # Filter for future times, and cap at required
    future = filter_future_signals(

        ranked,

        start_min,

        end_min,

        required
    )

    # Count how many we actually have
    available = len(future)

    # If fewer than required, we still return what we have
    if available < required:
        print(colored(f"⚠️ Only {available} qualified setups found (requested {required}).", "yellow"))

    return future, available


# ==========================================================
# FINAL OUTPUT
# ==========================================================

def print_final_output(
    signals,
    today_date,
    backtest_days,
    requested,
    available
):

    display_date = datetime.strptime(
        today_date,
        "%Y-%m-%d"
    ).strftime(
        "%d-%m-%Y"
    )


    print()

    print(
        f"DATE: {display_date}"
    )

    print(
        "TIMEZONE: UTC+6"
    )

    print(
        "TIMEFRAME: M1"
    )

    print(
        f"BACKTEST: {backtest_days} Days"
    )

    if available < requested:
        print(f"QUALIFIED: {available} signals (requested {requested})")
    else:
        print(f"QUALIFIED: {available} signals")

    print(
        "━━━━━━━━━━━━━━━━━━"
    )


    if not signals:

        print(
            colored("NO SIGNAL", "red")
        )

    else:

        signals.sort(
            key=lambda x:
            x["minute"]
        )


        for signal in signals:

            pair = (
                signal["pair"]
                .replace(
                    "_",
                    "/"
                )
            )


            print(
                f"M1;"
                f"{pair};"
                f"{signal['time']};"
                f"{signal['direction']}"
            )


    print(
        "━━━━━━━━━━━━━━━━━━"
    )

    print()


# ==========================================================
# MAIN
# ==========================================================

def main():

    # ======================================================
    # LOGO (RED)
    # ======================================================

    print(
        colored(
r"""
███╗   ██╗██╗   ██╗███╗   ███╗███████╗██████╗  ██████╗ 
████╗  ██║██║   ██║████╗ ████║██╔════╝██╔══██╗██╔═══██╗
██╔██╗ ██║██║   ██║██╔████╔██║█████╗  ██████╔╝██║   ██║
██║╚██╗██║██║   ██║██║╚██╔╝██║██╔══╝  ██╔══██╗██║   ██║
██║ ╚████║╚██████╔╝██║ ╚═╝ ██║███████╗██║  ██║╚██████╔╝
╚═╝  ╚═══╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝ 
""",
            "red"
        )
    )


    print(
        colored(
            "NUMERO — SIGNAL PROVIDER",
            "bold red"
        )
    )

    print()


    # ======================================================
    # USER INPUT
    # ======================================================

    start_time = input(
        "START TIME (HH:MM UTC+6): "
    ).strip()


    end_time = input(
        "END TIME (HH:MM UTC+6): "
    ).strip()


    if not valid_time(start_time):

        print(
            colored(
                "Invalid START TIME.",
                "red"
            )
        )

        return


    if not valid_time(end_time):

        print(
            colored(
                "Invalid END TIME.",
                "red"
            )
        )

        return


    try:

        backtest_days = int(
            input(
                "BACKTEST DAYS: "
            ).strip()
        )

    except Exception:

        print(
            colored(
                "Invalid BACKTEST DAYS.",
                "red"
            )
        )

        return


    try:

        required = int(
            input(
                "REQUIRED SIGNAL COUNT: "
            ).strip()
        )

    except Exception:

        print(
            colored(
                "Invalid SIGNAL COUNT.",
                "red"
            )
        )

        return


    if backtest_days < 1:

        print(
            colored(
                "BACKTEST DAYS must be >= 1.",
                "red"
            )
        )

        return


    if required < 1:

        print(
            colored(
                "REQUIRED SIGNAL COUNT must be >= 1.",
                "red"
            )
        )

        return


    # ======================================================
    # TIME RANGE
    # ======================================================

    start_min = time_to_minutes(
        start_time
    )

    end_min = time_to_minutes(
        end_time
    )


    # ======================================================
    # TODAY
    # ======================================================

    now_bd = datetime.now(
        BD_TIMEZONE
    )


    today_date = now_bd.strftime(
        "%Y-%m-%d"
    )


    # ======================================================
    # HISTORICAL RANGE
    # ======================================================

    historical_end_bd = (
        date_to_datetime(
            today_date
        )
        - timedelta(
            minutes=1
        )
    )


    historical_start_bd = (
        historical_end_bd
        - timedelta(
            days=backtest_days
        )
    )


    historical_start_utc = (
        historical_start_bd.astimezone(
            UTC
        )
    )


    historical_end_utc = (
        historical_end_bd.astimezone(
            UTC
        )
    )


    # ======================================================
    # LOAD DATA
    # ======================================================

    market = load_market_history(

        historical_start_utc,

        historical_end_utc
    )


    total_candles = sum(

        len(candles)

        for candles in market.values()
    )


    if total_candles < 100:

        print(
            colored(
                "Not enough historical data.",
                "red"
            )
        )

        return


    # ======================================================
    # GENERATE
    # ======================================================

    signals, available = generate_future_signals(

        market,

        start_min,

        end_min,

        required,

        today_date
    )


    # ======================================================
    # FINAL OUTPUT
    # ======================================================

    print_final_output(

        signals,

        today_date,

        backtest_days,

        required,

        available
    )


# ==========================================================
# RUN
# ==========================================================

if __name__ == "__main__":

    main()