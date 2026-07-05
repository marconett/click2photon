import asyncio
import sys
import csv
from datetime import datetime

csv.field_size_limit(sys.maxsize)
from serial import Serial, SerialException
from serial.serialutil import PortNotOpenError
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML


class CSVHandler:
    def __init__(self, output_path: str, headers: list):
        self.output_path = output_path
        self.headers = headers
        self.csv_file = None
        self.csv_writer = None
        self.setup_csv_file()

    def setup_csv_file(self):
        file_needs_headers = False

        try:
            with open(self.output_path, 'r') as f:
                first_line = f.readline().strip()
                if not first_line:
                    file_needs_headers = True
        except FileNotFoundError:
            file_needs_headers = True

        self.csv_file = open(self.output_path, 'a', newline='')
        self.csv_writer = csv.writer(self.csv_file)

        if file_needs_headers:
            self.csv_writer.writerow(self.headers)
            self.csv_file.flush()

    def write(self, line: str):
        csv_reader = csv.reader([line])
        row = next(csv_reader)
        self.csv_writer.writerow(row)
        self.csv_file.flush()

    def close(self):
        if self.csv_file:
            self.csv_file.close()


class SerialTerminal:
    def __init__(self, port: str, baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.serial_connected = False
        self.session = PromptSession("(latency-tester) > ")
        self.should_exit = False
        self.csv_handler = None

    async def connect(self):
        try:
            self.serial = Serial(self.port, self.baudrate, timeout=0.1)
            self.serial_connected = True
            print_formatted_text(HTML("<ansiyellow>Connected</ansiyellow>"))
        except Exception as e:
            if isinstance(e, SerialException):
                print_formatted_text(HTML("<ansired>Reconnecting ...</ansired>"))
                await asyncio.sleep(1)
                await self.connect()

    async def disconnect(self):
        self.serial_connected = False
        if self.serial and self.serial.is_open:
            await asyncio.to_thread(self.serial.close)
        print_formatted_text(HTML("<ansiyellow>Disconnected</ansiyellow>"))

    async def write_serial(self, command: str):
        try:
            await asyncio.to_thread(self.serial.write, command)
        except Exception as e:
            if isinstance(e, PortNotOpenError):
              print_formatted_text(HTML("<ansiyellow>Not connected</ansiyellow>"))
            else:
              print_formatted_text(HTML(f"<ansired>Error writing to serial: {e}</ansired>"))

    async def read_serial(self):
        while not self.should_exit:
            if self.serial_connected:
                try:
                    if self.serial and self.serial.in_waiting:
                        data = await asyncio.to_thread(self.serial.readline)
                        if data:
                            line = data.decode('utf-8', errors='ignore').strip()
                            if line:
                                if line.startswith("CSV"):
                                    csv_line = line[3:].strip()
                                    if csv_line and self.csv_handler:
                                        self.csv_handler.write(csv_line)
                                elif line == "DONE":
                                    if self.csv_handler:
                                        print_formatted_text(HTML(f"<ansigreen>Session complete</ansigreen>"))
                                        self.csv_handler.close()
                                        self.csv_handler = None
                                else:
                                    print(f"\t{line}")
                    else:
                        await asyncio.sleep(0.01)
                except Exception as e:
                    self.serial_connected = False
                    if isinstance(e, OSError):
                        print_formatted_text(HTML("<ansired>Connection lost</ansired>"))
                        await self.connect()
                    else:
                        print_formatted_text(HTML(f"<ansired>Error reading serial: {e}</ansired>"))
                        await asyncio.sleep(0.1)
            else:
                await asyncio.sleep(0.1)

    async def interactive_shell(self):
        while not self.should_exit:
            try:
                command = await self.session.prompt_async()
                command = command.strip().lower()

                if command == 'start':
                    if self.csv_handler is None:
                        timestamp = datetime.now().strftime('%y%m%d-%H-%M-%S')
                        filename = f"{timestamp}_session.csv"
                        self.csv_handler = CSVHandler("output/" + filename, ['clickTime', 'timeTaken', 'sampleCount', 'preClickSamples', 'samples'])
                        print_formatted_text(HTML(f"<ansigreen>Starting session: {filename}</ansigreen>"))
                    await self.write_serial(b'1')

                elif command == 'stop':
                    await self.write_serial(b'0')
                    if self.csv_handler:
                        self.csv_handler.close()
                        self.csv_handler = None

                elif command in ['debug', 'd']:
                    await self.write_serial(b'd')

                elif command.startswith('interval ') or command.startswith('i '):
                    try:
                        value = float(command.split()[1])
                        await self.write_serial(f'i{value}'.encode())
                    except (IndexError, ValueError):
                        print_formatted_text(HTML("<ansiyellow>Usage: interval <float> (seconds)</ansiyellow>"))

                elif command.startswith('clicks ') or command.startswith('c '):
                    try:
                        value = int(command.split()[1])
                        await self.write_serial(f'c{value}'.encode())
                    except (IndexError, ValueError):
                        print_formatted_text(HTML("<ansiyellow>Usage: clicks <integer></ansiyellow>"))

                elif command in ['disconnect']:
                    if self.serial_connected:
                        await self.disconnect()
                        if self.csv_handler:
                            self.csv_handler.close()
                            self.csv_handler = None
                    else:
                        print_formatted_text(HTML("<ansiyellow>Not connected</ansiyellow>"))

                elif command in ['connect']:
                    if not self.serial_connected:
                        await self.connect()
                    else:
                        print_formatted_text(HTML("<ansiyellow>Already connected</ansiyellow>"))

                elif command in ['help']:
                    self.print_help_text()

                elif command in ['exit', 'quit']:
                    if self.csv_handler:
                        self.csv_handler.close()
                        self.csv_handler = None
                    await self.disconnect()
                    self.should_exit = True

            except (EOFError, KeyboardInterrupt):
                # Close CSV handler
                if self.csv_handler:
                    self.csv_handler.close()
                    self.csv_handler = None
                await self.disconnect()
                self.should_exit = True

    def print_help_text(self):
        help_message = HTML(
            "<ansigreen>Available commands:</ansigreen>\n"
            "<ansiblue>start</ansiblue> - Start latency test (3s countdown)\n"
            "<ansiblue>stop</ansiblue> - Stop test and debug mode\n"
            "<ansiblue>debug</ansiblue> - Enable debug mode\n"
            "<ansiblue>interval &lt;float&gt;</ansiblue> - Set time between clicks (seconds)\n"
            "<ansiblue>clicks &lt;integer&gt;</ansiblue> - Set click count\n"
            "<ansiblue>connect</ansiblue> - Connect to the serial port\n"
            "<ansiblue>disconnect</ansiblue> - Disconnect from the serial port\n"
            "<ansiblue>help</ansiblue> - Print this help text\n"
            "<ansiblue>exit</ansiblue> - Exit the terminal"
        )
        print_formatted_text(help_message)

    async def run(self):
        await self.connect()

        try:
            with patch_stdout():
                await asyncio.gather(
                    self.read_serial(),
                    self.interactive_shell()
                )
        finally:
            await self.cleanup()

    async def cleanup(self):
        self.serial_connected = False
        if self.serial:
            await asyncio.to_thread(self.serial.close)
        if self.csv_handler:
            self.csv_handler.close()


async def main():
    port = '/dev/cu.usbmodem101'
    baudrate = 115200

    terminal = SerialTerminal(port, baudrate)
    terminal.print_help_text()
    print_formatted_text(HTML(f"<ansiyellow>\nStarting terminal on {port} at {baudrate} baud</ansiyellow>"))

    await terminal.run()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(0)