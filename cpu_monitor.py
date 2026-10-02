import psutil
import time
import os


# ─────────────────────────────────────────────
# Screen
# ─────────────────────────────────────────────

def clear_screen():
    os.system("clear")


# ─────────────────────────────────────────────
# CPU Information
# ─────────────────────────────────────────────

def get_cpu_name():
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if line.startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except Exception:
        pass

    return "Unknown"


# ─────────────────────────────────────────────
# CPU Topology
# ─────────────────────────────────────────────

def get_topology():
    topology = {}

    cpu_path = "/sys/devices/system/cpu"

    cpus = [
        x for x in os.listdir(cpu_path)
        if x.startswith("cpu") and x[3:].isdigit()
    ]

    cpus.sort(key=lambda x: int(x[3:]))

    for cpu in cpus:
        cpu_num = int(cpu[3:])
        path = os.path.join(cpu_path, cpu, "topology")

        try:
            with open(os.path.join(path, "physical_package_id")) as f:
                socket = f.read().strip()

            with open(os.path.join(path, "core_id")) as f:
                core = f.read().strip()

            topology[cpu_num] = {
                "socket": socket,
                "core": core
            }

        except (FileNotFoundError, ValueError):
            continue

    return topology


def print_topology(topology):
    print("CPU TOPOLOGY")
    print("-" * 70)

    sockets = {}

    for cpu, info in topology.items():

        socket = info["socket"]
        core = info["core"]

        if socket not in sockets:
            sockets[socket] = {}

        if core not in sockets[socket]:
            sockets[socket][core] = []

        sockets[socket][core].append(cpu)

    for socket, cores in sockets.items():

        print(f"┌─ Socket {socket}")

        core_items = list(cores.items())

        for index, (core, cpus) in enumerate(core_items):

            if index == len(core_items) - 1:
                prefix = "└─"
            else:
                prefix = "├─"

            logical_cpus = "  ".join(
                f"CPU {cpu}" for cpu in cpus
            )

            print(
                f"│ {prefix} Core {core:>2} ── {logical_cpus}"
            )

    print()


# ─────────────────────────────────────────────
# Temperature
# ─────────────────────────────────────────────

def get_temperature():
    try:
        temps = psutil.sensors_temperatures()

        for name in ["coretemp", "k10temp", "cpu_thermal"]:

            if name in temps and temps[name]:
                return temps[name][0].current

        # Fallback
        for entries in temps.values():
            if entries:
                return entries[0].current

    except Exception:
        pass

    return None


# ─────────────────────────────────────────────
# Usage Bar
# ─────────────────────────────────────────────

def usage_bar(percent, width=20):

    filled = int((percent / 100) * width)

    return "[" + "█" * filled + "░" * (width - filled) + "]"


# ─────────────────────────────────────────────
# Main Dashboard
# ─────────────────────────────────────────────

def display():

    clear_screen()

    cpu_name = get_cpu_name()
    topology = get_topology()

    print("=" * 70)
    print("                         CPU MONITOR")
    print("=" * 70)

    print(f"CPU: {cpu_name}")

    # Topology statistics
    sockets = set()
    cores = set()

    for info in topology.values():

        sockets.add(info["socket"])
        cores.add(
            (info["socket"], info["core"])
        )

    print(
        f"Topology: {len(sockets)} Socket(s) | "
        f"{len(cores)} Physical Core(s) | "
        f"{len(topology)} Logical CPU(s)"
    )

    print()

    # ─────────────────────────────────────────
    # Topology
    # ─────────────────────────────────────────

    print_topology(topology)

    # ─────────────────────────────────────────
    # CPU Usage
    # ─────────────────────────────────────────

    usage = psutil.cpu_percent(
        interval=0.5,
        percpu=True
    )

    frequencies = psutil.cpu_freq(
        percpu=True
    )

    print("LIVE CPU STATUS")
    print("-" * 70)

    for cpu, percent in enumerate(usage):

        if frequencies and cpu < len(frequencies):
            freq = frequencies[cpu].current
        else:
            freq = 0

        if cpu in topology:
            core = topology[cpu]["core"]

            print(
                f"CPU {cpu:2d} "
                f"(Core {core:>2})  "
                f"{usage_bar(percent)} "
                f"{percent:5.1f}%  "
                f"{freq:7.0f} MHz"
            )

        else:

            print(
                f"CPU {cpu:2d}  "
                f"{usage_bar(percent)} "
                f"{percent:5.1f}%  "
                f"{freq:7.0f} MHz"
            )

    print()

    # ─────────────────────────────────────────
    # Temperature
    # ─────────────────────────────────────────

    temperature = get_temperature()

    print("TEMPERATURE")
    print("-" * 70)

    if temperature is not None:
        print(
            f"CPU Temperature: "
            f"{temperature:.1f} °C"
        )
    else:
        print(
            "CPU Temperature: "
            "Sensor unavailable"
        )

    print()

    # ─────────────────────────────────────────
    # RAM
    # ─────────────────────────────────────────

    memory = psutil.virtual_memory()

    used = memory.used / (1024 ** 3)
    total = memory.total / (1024 ** 3)

    print("MEMORY")
    print("-" * 70)

    print(
        f"RAM Usage: {memory.percent:.1f}% "
        f"({used:.2f} GB / {total:.2f} GB)"
    )

    print()

    print("=" * 70)
    print("Refreshing every 1 second | Ctrl+C to exit")


# ─────────────────────────────────────────────
# Run
# ─────────────────────────────────────────────

try:

    while True:

        display()
        time.sleep(1)

except KeyboardInterrupt:

    clear_screen()
    print("CPU Monitor stopped.")
