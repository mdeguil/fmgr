import os
import shutil
from abc import ABC, abstractmethod

""" File Manager Console Application 
    Generated with Claude 3.5 Haiku
    With 2 prompts : 
        Génère un programme console python qui permet d'explorer les fichiers, 
        en sélectionner pour copier, déplacer et supprimer les fichiers sélectionnés. 
        Une classe "métier" regroupe les fonctions de sélection, copie, déplacement 
        et suppression.

        Refactoring (SRP) : l'exploration (affichage, navigation) est sortie de
        FileManager dans la classe FileExplorer ; FileManager ne gère plus que
        la copie, le déplacement et la suppression.

        Inversion de contrôle : FileManager reçoit par son constructeur des
        abstractions (FileSelection, FileSystem, Output) au lieu d'utiliser
        directement os, shutil et print, ce qui le rend testable.

        Deux rectifications : il faudrait passer le code et l'interface en anglais 
        et sortir la sélection de la classe "métier"
"""


class FileSelection(ABC):
    """Abstraction of a file selection (what FileManager needs from a selector)"""

    @abstractmethod
    def get_selected_files(self):
        """Return the list of currently selected files"""

    @abstractmethod
    def clear_selection(self):
        """Clear the current file selection"""


class FileSystem(ABC):
    """Abstraction of the file system operations used by FileManager"""

    @abstractmethod
    def exists(self, path): ...

    @abstractmethod
    def is_file(self, path): ...

    @abstractmethod
    def is_dir(self, path): ...

    @abstractmethod
    def copy(self, source, destination): ...

    @abstractmethod
    def move(self, source, destination): ...

    @abstractmethod
    def remove_file(self, path): ...

    @abstractmethod
    def remove_tree(self, path): ...


class Output(ABC):
    """Abstraction of the user interface output"""

    @abstractmethod
    def show(self, message): ...


class OsFileSystem(FileSystem):
    """FileSystem backed by os and shutil"""

    def exists(self, path):
        return os.path.exists(path)

    def is_file(self, path):
        return os.path.isfile(path)

    def is_dir(self, path):
        return os.path.isdir(path)

    def copy(self, source, destination):
        shutil.copy2(source, destination)

    def move(self, source, destination):
        shutil.move(source, destination)

    def remove_file(self, path):
        os.remove(path)

    def remove_tree(self, path):
        shutil.rmtree(path)


class ConsoleOutput(Output):
    """Output printing to the console"""

    def show(self, message):
        print(message)


class FileSelector(FileSelection):
    def __init__(self):
        self.selected_files = []
        self.current_directory_contents = []

    def load_directory_contents(self, directory_path):
        """Load the contents of a directory"""
        try:
            self.current_directory_contents = os.listdir(directory_path)
            return self.current_directory_contents
        except Exception as e:
            print(f"Error loading directory contents: {e}")
            return []

    def select_files_by_indices(self, indices, directory_path):
        """Select files based on indices"""
        try:
            # Convert input string to list of indices
            selected_indices = [int(i.strip()) for i in indices.split(',')]
            
            # Reset previous selection
            self.selected_files.clear()
            
            # Select files
            for index in selected_indices:
                if 0 <= index < len(self.current_directory_contents):
                    full_path = os.path.join(directory_path, self.current_directory_contents[index])
                    self.selected_files.append(full_path)
            
            print("Selected files:")
            for file in self.selected_files:
                print(f" - {os.path.basename(file)}")
            
            return self.selected_files
        except ValueError:
            print("Invalid input. Please enter valid indices.")
            return []
        except Exception as e:
            print(f"Error selecting files: {e}")
            return []

    def get_selected_files(self):
        """Return the list of currently selected files"""
        return self.selected_files

    def clear_selection(self):
        """Clear the current file selection"""
        self.selected_files.clear()


class FileExplorer:
    def __init__(self, file_selector):
        self.current_path = os.path.expanduser('~')
        self.file_selector = file_selector

    def display_directory_contents(self):
        """Display contents of the current directory"""
        try:
            contents = self.file_selector.load_directory_contents(self.current_path)
            print(f"\nCurrent Directory: {self.current_path}")
            print("-" * 50)
            for index, element in enumerate(contents):
                full_path = os.path.join(self.current_path, element)
                element_type = "📁 Folder" if os.path.isdir(full_path) else "📄 File"
                print(f"{index}. {element_type}: {element}")
        except PermissionError:
            print("Access denied to this directory.")
        except Exception as e:
            print(f"Error: {e}")

    def navigate(self, index):
        """Navigate to a subdirectory"""
        try:
            contents = os.listdir(self.current_path)
            selected_element = contents[index]
            full_path = os.path.join(self.current_path, selected_element)
            
            if os.path.isdir(full_path):
                self.current_path = full_path
                self.display_directory_contents()
            else:
                print(f"Cannot open file {selected_element}")
        except Exception as e:
            print(f"Navigation error: {e}")

    def go_to_parent_directory(self):
        """Move to the parent directory"""
        self.current_path = os.path.dirname(self.current_path)
        self.display_directory_contents()


class FileManager:
    def __init__(self, selection: FileSelection, filesystem: FileSystem, output: Output):
        self.selection = selection
        self.filesystem = filesystem
        self.output = output

    def copy_files(self, destination):
        """Copy selected files"""
        try:
            selected_files = self.selection.get_selected_files()
            for file in selected_files:
                if self.filesystem.exists(file):
                    self.filesystem.copy(file, destination)
            self.output.show(f"{len(selected_files)} file(s) copied")
            self.selection.clear_selection()
        except Exception as e:
            self.output.show(f"Copy error: {e}")

    def move_files(self, destination):
        """Move selected files"""
        try:
            selected_files = self.selection.get_selected_files()
            for file in selected_files:
                if self.filesystem.exists(file):
                    self.filesystem.move(file, destination)
            self.output.show(f"{len(selected_files)} file(s) moved")
            self.selection.clear_selection()
        except Exception as e:
            self.output.show(f"Move error: {e}")

    def delete_files(self):
        """Delete selected files"""
        try:
            selected_files = self.selection.get_selected_files()
            for file in selected_files:
                if self.filesystem.is_file(file):
                    self.filesystem.remove_file(file)
                elif self.filesystem.is_dir(file):
                    self.filesystem.remove_tree(file)
            self.output.show(f"{len(selected_files)} file(s)/folder(s) deleted")
            self.selection.clear_selection()
        except Exception as e:
            self.output.show(f"Delete error: {e}")


def main_menu():
    file_selector = FileSelector()
    file_explorer = FileExplorer(file_selector)
    file_manager = FileManager(file_selector, OsFileSystem(), ConsoleOutput())

    while True:
        print("\n--- File Explorer ---")
        print("1. Display Directory")
        print("2. Navigate")
        print("3. Go to Parent Directory")
        print("4. Select Files")
        print("5. Copy")
        print("6. Move")
        print("7. Delete")
        print("8. Quit")
        
        choice = input("Your choice: ")
        
        try:
            if choice == '1':
                file_explorer.display_directory_contents()

            elif choice == '2':
                index = int(input("Enter navigation index: "))
                file_explorer.navigate(index)

            elif choice == '3':
                file_explorer.go_to_parent_directory()

            elif choice == '4':
                file_explorer.display_directory_contents()
                indices = input("Enter file indices to select (comma-separated): ")
                file_selector.select_files_by_indices(indices, file_explorer.current_path)
            
            elif choice == '5':
                dest = input("Enter destination path for copying: ")
                file_manager.copy_files(dest)
            
            elif choice == '6':
                dest = input("Enter destination path for moving: ")
                file_manager.move_files(dest)
            
            elif choice == '7':
                file_manager.delete_files()
            
            elif choice == '8':
                print("Goodbye!")
                break
            
            else:
                print("Invalid choice")
        
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main_menu()