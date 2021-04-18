# coding=utf-8
import sys
from argparse import ArgumentParser
from hashlib import md5
from os import path
from os import remove
from os import rename
from os import walk


def parse_arguments():
    parser = ArgumentParser()
    parser.add_argument('directory', type=str, nargs='?')
    return parser.parse_args()


class DuplicateFileHandler:

    def __init__(self):
        self.directory = parse_arguments().directory
        self.file_extension = None
        self.sorting_option = None
        self.file_sizes = {}
        self.same_size_files = {}
        self.same_hash_files = {}
        self.duplicates = []
        self.dispatcher()

    def dispatcher(self):
        if self.directory is None:
            self.exit('Directory is not specified')
        file_format = input('Enter file format:\n')
        self.file_extension = file_format if file_format else None
        self.get_option()
        self.get_files()
        self.print_file_size()
        self.check_for_duplicates()
        self.print_file_hashes()
        self.delete_files()

    def get_option(self):
        options = {'1': True, '2': False}
        user_input = input(
            'Size sorting options:\n'
            '1. Descending\n'
            '2. Ascending\n'
            'Enter a sorting option:\n'
            )
        self.sorting_option = options.get(user_input)
        if self.sorting_option is None:
            print('\nWrong option\n')
            return self.get_option()

    def get_files(self):
        for root, dirs, files in walk(self.directory):
            for name in files:
                _, extension = path.splitext(name)
                if self.valid_extension(extension):
                    filepath = path.join(root, name)
                    self.process_files(filepath)

    def process_files(self, filepath):
        file_size = path.getsize(filepath)
        rename(filepath, filepath.lower())  # stages 2-4 tests 4 & 5
        if file_size in self.file_sizes:
            self.file_sizes[file_size].append(filepath)
        else:
            self.file_sizes[file_size] = [filepath]

    def valid_extension(self, extension):
        return extension.endswith(
            self.file_extension
            ) if self.file_extension is not None else True

    @staticmethod
    def exit(message=None):
        if message is not None:
            print(message)
        sys.exit(0)

    def print_file_size(self):
        self.same_size_files = {
            file_size: file_paths for file_size, file_paths
            in self.file_sizes.items() if len(file_paths) > 1
            }
        for size in sorted(self.same_size_files, reverse=self.sorting_option):
            print(f'\n{size} bytes')
            print(*self.same_size_files[size], sep='\n')

    def check_for_duplicates(self):
        options = {
            'yes': self.process_files_for_hash,
            'no': self.exit,
            }
        user_input = input('Check for duplicates?\n')
        if user_input in options:
            return options.get(user_input)()
        print('Wrong option!\n')
        return self.check_for_duplicates()

    def process_files_for_hash(self):
        hashed_files = {}
        for size, file_paths in self.same_size_files.items():
            for filepath in file_paths:
                file_hash = self.get_hash(filepath)
                if size in hashed_files and file_hash in hashed_files[size]:
                    hashed_files[size][file_hash].append(filepath)
                else:
                    if size in hashed_files:
                        hashed_files[size].update({file_hash: [filepath]})
                    else:
                        hashed_files[size] = {file_hash: [filepath]}

        for size, file_hashes in hashed_files.items():
            for file_hash, paths in file_hashes.items():
                if len(paths) > 1:
                    if size in self.same_hash_files:
                        self.same_hash_files[size].update({file_hash: paths})
                    else:
                        self.same_hash_files[size] = {file_hash: paths}

    @staticmethod
    def get_hash(filepath):
        with open(filepath, 'rb') as file:
            file_hash = md5()
            file_hash.update(file.read())
            return file_hash.hexdigest()

    def print_file_hashes(self):
        if not self.same_hash_files:
            print('No duplicates found.')
            self.exit()
        n = 1
        for size in sorted(self.same_hash_files, reverse=self.sorting_option):
            print(f'\n{size} bytes')
            for file_hash, paths in self.same_hash_files[size].items():
                print(f'Hash: {file_hash}')
                for num, file_path in enumerate(paths, n):
                    print(f'{num}. {file_path}')
                    self.duplicates.append(file_path)
                n += len(paths)

    def delete_files(self):
        options = {
            'yes': self.process_files_to_delete,
            'no': self.exit,
            }
        user_input = input('Delete files?\n')
        if user_input in options:
            return options.get(user_input)()
        print('Wrong option!\n')
        return self.delete_files()

    def process_files_to_delete(self):
        user_input = input('Enter file numbers to delete:\n')
        files_to_delete_numbers = user_input.split()
        if files_to_delete_numbers:
            file_numbers = {
                int(i) for i in files_to_delete_numbers if i.isdigit()
                }
            if len(files_to_delete_numbers) == len(file_numbers):
                duplicate_file_numbers = set(
                    range(1, len(self.duplicates) + 1)
                    )
                if file_numbers & duplicate_file_numbers == file_numbers:
                    total_freed_space = 0
                    for file_number in file_numbers:
                        file = self.duplicates[file_number - 1]
                        total_freed_space += path.getsize(file)
                        remove(file)
                    print(f'Total freed up space: {total_freed_space} bytes')
        print('\nWrong format\n')
        return self.process_files_to_delete()


if __name__ == '__main__':
    DuplicateFileHandler()
