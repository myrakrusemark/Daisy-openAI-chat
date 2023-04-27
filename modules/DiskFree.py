import psutil
import humanize
import platform

class DiskFree:
	"""
	Description: A description of this class and its pip capabilities.
	Module Hook: The hook in the program where method main() will be passed into.
	"""
	description = "A module for checking available computer resources."
	module_hook = "Chat_request_inner"
	tool_form_name = "Available Computer Resources"
	tool_form_description = "A module that describes the available computer resources: Hard disk space, memory, CPU utilization, and CPU temperature."
	tool_form_argument = "Drive letter (Or 'None')"

	def __init__(self, ml):
		self.ml = ml
		self.ch = ml.ch

		self.match = None


	def main(self, arg, stop_event):
		# Get disk free space
		disk_partitions = psutil.disk_partitions(all=True)
		disk_free_space = {}

		for partition in disk_partitions:
			try:
				partition_usage = psutil.disk_usage(partition.mountpoint)
				disk_free_space[partition.device] = partition_usage.free
			except:
				pass

		# Get free memory
		mem = psutil.virtual_memory()
		mem_free = mem.available

		# Get CPU utilization
		cpu_percent = psutil.cpu_percent()

		# Get CPU temperature (not supported on all systems)
		try:
			if platform.system() == "Linux":
				with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
					temp = int(f.read()) / 1000
			else:
				temp = "N/A"
		except:
			temp = "N/A"

		# Format the output using humanize
		formatted_output = "System Information:\n"
		formatted_output += f"  Disk free space:\n"
		for device, free_space in disk_free_space.items():
			formatted_output += f"    {device}: {humanize.naturalsize(free_space)}\n"
		formatted_output += f"  Free memory: {humanize.naturalsize(mem_free)}\n"
		formatted_output += f"  CPU utilization: {cpu_percent}%\n"
		formatted_output += f"  CPU temperature: {temp}\n"

		return formatted_output