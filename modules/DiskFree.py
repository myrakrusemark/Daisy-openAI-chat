import psutil
import humanize
import platform

class DiskFree:
    description = "A module for checking available computer resources."
    module_hook = "Chat_request_inner"
    tool_form_name = "Available Computer Resources"
    tool_form_description = "A module that describes the available computer resources: Hard disk space, memory, CPU utilization, and CPU temperature."
    tool_form_argument = "Drive letter (Or 'None')"

    def __init__(self, ml):
        self.ml = ml
        self.ch = ml.ch

    def main(self, arg, stop_event):
        disk_free_space = self.get_disk_free_space()
        mem_free = self.get_free_memory()
        cpu_percent = self.get_cpu_utilization()
        temp = self.get_cpu_temperature()

        formatted_output = self.format_output(disk_free_space, mem_free, cpu_percent, temp)
        return formatted_output

    def get_disk_free_space(self):
        disk_partitions = psutil.disk_partitions(all=True)
        disk_free_space = {}

        for partition in disk_partitions:
            try:
                partition_usage = psutil.disk_usage(partition.mountpoint)
                disk_free_space[partition.device] = partition_usage.free
            except:
                pass

        return disk_free_space

    def get_free_memory(self):
        mem = psutil.virtual_memory()
        return mem.available

    def get_cpu_utilization(self):
        return psutil.cpu_percent()

    def get_cpu_temperature(self):
        try:
            if platform.system() == "Linux":
                with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                    temp = int(f.read()) / 1000
            else:
                temp = "N/A"
        except:
            temp = "N/A"

        return temp

    def format_output(self, disk_free_space, mem_free, cpu_percent, temp):
        formatted_output = "System Information:\n"
        formatted_output += f"  Disk free space:\n"
        for device, free_space in disk_free_space.items():
            formatted_output += f"    {device}: {humanize.naturalsize(free_space)}\n"
        formatted_output += f"  Free memory: {humanize.naturalsize(mem_free)}\n"
        formatted_output += f"  CPU utilization: {cpu_percent}%\n"
        formatted_output += f"  CPU temperature: {temp}\n"

        return formatted_output
