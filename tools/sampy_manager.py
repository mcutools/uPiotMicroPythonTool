# This file is part of the uPiot project, https://github.com/gepd/upiot/
#
# MIT License
#
# Copyright (c) 2017 GEPD
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sublime

from os import path, mkdir
from ..tools import check_sidebar_folder, make_folder as mkfolder
from ..tools import message, serial, errors, status_color
from ..tools.sampy import Sampy
from ..tools.ampy import files

txt = None
port = None


def start_sampy(quiet=False):
    """
    Opens the sampy connection in the selected port. If already is a serial
    connection running it will look into it and close it.

    Returns:
        Sampy -- Sampy object
    """
    global txt
    global port

    port = serial.selected_port()

    # close the current connection in open port
    if(port in serial.in_use and not quiet):
        run_serial = serial.serial_dict[port]
        run_serial.stop_task()

    # message printer
    txt = message.open(port)
    txt.set_focus()

    if(port and not quiet):
        try:
            return Sampy(port, data_consumer=txt.print)
        except file.PyboardError as e:
            from sys import exit

            if('failed to access' in str(e)):
                txt.print(errors.serialError_noaccess)
                status_color.remove()
            exit(0)


def finished_action():
    """
    This function will be called after an action is finished, and will
    re-open the serial connection if was open.
    """
    global port

    serial.establish_connection(port)

    # opens the console window
    sublime.active_window().run_command('upiot_console_write')


def run_file(filepath):
    """Run file in device

    Runs the given file in the selected device.

    Arguments:
        filepath {str} -- file path
    """
    global txt

    sampy = start_sampy()

    # print command name
    file = path.basename(filepath)

    head = '\n\n>> Run {0}\n\n"ctrl+shift+c" to stop the script.\n---'
    txt.print(head.format(file))

    try:
        sampy.run(filepath)
        txt.print("\n[done]")
    except AttributeError as e:
        txt.print("\n\nOpening console...\nRun the command again.")

    finished_action()


def list_files():
    """List of files in device

    Shows the list of files (and folders) from the selected device
    """
    sampy = start_sampy()

    txt.print('\n\n>> sampy ls\n')

    try:
        for filename in sampy.ls():
            txt.print('\n' + filename)
    except AttributeError as e:
        txt.print("\n\nOpening console...\nRun the command again.")

    finished_action()


def get_file(filename):
    """Get file from device

    Gets the given file from the selected device

    Arguments:
        filename {str} -- name of the file
    """
    sampy = start_sampy()

    txt.print('\n\n>> get {0}'.format(filename))
    try:
        output = sampy.get(filename)
    except RuntimeError as e:
        output = str(e)

    output = output.replace('\r\n', '\n').replace('\r', '\n')

    txt.print('\n\n' + output)

    finished_action()


def get_files(destination):
    """Get files from devices

    Gets all the files in the device and stored in the selected destination
    path.
    """
    error = False
    sampy = start_sampy()

    destination = path.normpath(destination)
    mkfolder(destination)

    txt.print('\n\n>> Storing in {0}\n'.format(destination))

    try:
        for filename in sampy.ls():
            txt.print('\nRetrieving ' + filename + ' ...')

            filepath = path.normpath(path.join(destination, filename))
            if(filename.endswith('/')):
                if(not path.exists(filepath)):
                    mkdir(filepath)
            else:
                with open(filepath, 'wb') as file:
                    sampy.get(filename, file)
        output = '[done]'
    except AttributeError as e:
        output = 'Opening console...\nRun the command again.'
        error = True

    txt.print('\n\n' + output)

    finished_action()

    if(error):
        return

    if(check_sidebar_folder(destination)):
        return

    caption = "files retrieved, would you like to " \
        "add the folder to your current proyect?"
    answer = sublime.yes_no_cancel_dialog(caption, "Add", "Append")

    if(answer == sublime.DIALOG_CANCEL):
        return

    if(answer == sublime.DIALOG_YES):
        append = False
    elif(answer == sublime.DIALOG_NO):
        append = True

    options = {'folder': destination, 'append': append}
    sublime.active_window().run_command('upiot_add_project', options)


def put_file(filepath):
    """Put given file in device

    Puts the given in the selected device

    Arguments:
        filepath {str} -- path of the file to put
    """
    sampy = start_sampy()

    try:
        file = path.basename(filepath)
        txt.print('\n\n>> put {0}'.format(file))

        try:
            sampy.put(path.normpath(filepath))
            output = '[done]'
        except FileNotFoundError as e:
            output = str(e)
        except files.PyboardError as e:
            txt.print('\n\nError putting the file.\nReason: ' + str(e))
            return finished_action()
        except AttributeError as e:
            output = 'Opening console...\nRun the command again.'
        txt.print('\n\n' + output)

    except TypeError as e:
        txt.print("\n\n" + str(e))

    finished_action()


def remove_file(filepath):
    """Remove file in device

    Removes the given file in the selected device

    Arguments:
        filepath {str} -- file to remove
    """
    sampy = start_sampy()

    file = path.basename(filepath)
    txt.print('\n\n>> rm {0}'.format(file))

    try:
        sampy.rm(filepath)
        output = '[done]'
    except RuntimeError as e:
        output = str(e)
    except AttributeError as e:
        output = 'Opening console...\nRun the command again.'

    txt.print('\n\n' + output)

    finished_action()


def make_folder(folder_name):
    """Create folder

    Makes a folder in the selected device

    Arguments:
        folder_name {str} -- folder name
    """
    sampy = start_sampy()

    txt.print('\n\n>> mkdir {0}'.format(folder_name))

    try:
        sampy.mkdir(folder_name)
        output = '[done]'
    except files.DirectoryExistsError as e:
        output = str(e)
    except AttributeError as e:
        output = 'Opening console...\nRun the command again.'

    txt.print('\n\n' + output)

    finished_action()


def remove_folder(folder_name):
    """Remove folder from device

    Removes the given folder in the selected device

    Arguments:
        folder_name {str} -- folder to remvoe
    """
    sampy = start_sampy()

    txt.print('\n\n>> rmdir {0}'.format(folder_name))

    try:
        sampy.rmdir(folder_name)
        output = '[done]'
    except RuntimeError as e:
        output = str(e)
    except AttributeError as e:
        output = 'Opening console...\nRun the command again.'

    txt.print('\n\n' + output)

    finished_action()


def help():
    """Show commands help

    Displays the sampy command usage
    """
    start_sampy(quiet=True)

    _help = """\n\nUsage: sampy COMMAND [ARGS]...

        sampy - Sublime Text version of ampy MicroPython Tool

        Sampy is the Sublime Text version of the ampy tool developed
        by Adafruit. It's a tool to control MicroPython boards over a
        serial connection.

        Sampy will allow you to manipulate files on the board's internal
        filesystem and even run scripts from the console or from the
        Sublime Text interface.

        Commands:
           get\t\t\tRetrieve a file from the board.
           ls\t\t\tList the contens on the board.
           mkdir\t\tCreate a directory on the board.
           put\t\t\tPut a file or folder and its contents on the board.
           reset\t\tPerform soft reset/reboot of the board.
           rm\t\t\tRemove a file from the board.
           rmdir\t\tForcefully remove a folder and all its content from board
           run\t\t\tRun a script and print it's output
        """.replace('    ', '')

    txt.print(_help)
    finished_action()
