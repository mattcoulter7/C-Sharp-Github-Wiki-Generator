import os
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import filedialog
root = tk.Tk()
root.withdraw()

class XMLComment:
    def __init__(self,comment,statement):
        self.comment = comment
        self.parsed_comment = None
        self.summary = None
        self.parse_comment()

        self.statement = statement
        self.split_statement = self.statement.split(' ')

        self.title = None
        self.encapsulation = None
        self.parameters = None
        self.super_class = None
        self.type = None
        self.modifier = None
        self.parse_statement()

    def parse_statement(self):
        pass

    def parse_comment(self):
        self.parsed_comment = self.comment
        self.parsed_comment = self.parsed_comment.split('///')
        self.parsed_comment = self.parsed_comment[1:]
        self.parsed_comment = list(map(lambda line: line.strip(),self.parsed_comment))
        self.parsed_comment = '\\'.join(self.parsed_comment) # markdown new line
        self.parsed_comment = BeautifulSoup(self.parsed_comment)
        
        self.summary = self.parsed_comment.summary.text

    def get_markdown():
        pass

class XMLComment_Interface(XMLComment):
    def parse_statement(self):
        if self.split_statement[0] == 'interface':
            self.split_statement.insert(0,'private')
        self.title = self.split_statement[2]
        self.encapsulation = self.split_statement[0]

    def get_markdown():
        pass

class XMLComment_Class(XMLComment):
    def parse_statement(self):
        if self.split_statement[0] == 'class':
            self.split_statement.insert(0,'private')
        self.modifier = self.split_statement[1] if self.split_statement[1] == 'abstract' else None
        self.title = self.split_statement[2 if self.modifier is None else 3]
        self.encapsulation = self.split_statement[0]
        try:
            self.super_class = self.split_statement[self.split_statement.index(":") + 1]
        except ValueError:
            self.super_class = None

    def get_markdown():
        pass

class XMLComment_SubClass(XMLComment_Class):

    def get_markdown():
        pass


class XMLComment_Enum(XMLComment):
    def parse_statement(self):
        if self.split_statement[0] == 'enum':
            self.split_statement.insert(0,'private')
        self.title = self.split_statement[2]
        self.encapsulation = self.split_statement[0]

    def get_markdown():
        pass

class XMLComment_Function(XMLComment):
    def parse_statement(self):
        if self.split_statement[0] != 'private' and self.split_statement[0] != 'public' and self.split_statement[0] != 'protected':
            self.split_statement.insert(0,'private')
        self.modifier = self.split_statement[1] if self.split_statement[1] in ['abstract','override','virtual'] else None
        self.title = self.split_statement[2 if self.modifier is None else 3].split('(')[0]
        self.encapsulation = self.split_statement[0]
        self.parameters = self.statement.split('(')[1].split(')')[0].split(',')
        self.parameters = list(map(lambda param: param.strip(),self.parameters))
        self.parameters = list(filter(lambda param: param != '',self.parameters))
        self.type = self.split_statement[1]

    def get_markdown():
        pass
        
class XMLComment_Variable(XMLComment):
    def parse_statement(self):
        if self.split_statement[0] != 'private' and self.split_statement[0] != 'public' and self.split_statement[0] != 'protected':
            self.split_statement.insert(0,'private')
        self.encapsulation = self.split_statement[0]
        self.title = self.split_statement[2]
        self.type = self.split_statement[1]

    def get_markdown():
        pass

def determine_prop_type(statement):
    if 'class' in statement:
        return XMLComment_Class
    elif 'interface' in statement:
        return XMLComment_Interface
    elif 'enum' in statement:
        return XMLComment_Enum
    elif ');' in statement:
        return XMLComment_Variable
    elif '(' in statement and ')' in statement:
        return XMLComment_Function
    return XMLComment_Variable

def extract_comments(filepath):
    comments = []
    class_found = False
    with open(filepath) as f: 
        current_comment = None
        for line in f:
            line = line.strip()
            # comment detected
            if line.startswith("///"):
                current_comment = current_comment + line if current_comment is not None else line
            else:
                # comment finished
                if current_comment is not None:
                    if line == '': continue
                    if line.startswith('['): continue # ignore serialization etc.
                    
                    # determine which type of parser to use for the property
                    prop_type = determine_prop_type(line)

                    # handle class within classes
                    if prop_type == XMLComment_Class:
                        if class_found:
                            prop_type = XMLComment_SubClass
                        else:
                            class_found = True

                    prop_comment = prop_type(current_comment,line)
                    comments.append(prop_comment)
                    current_comment = None

    return comments


file_path = filedialog.askdirectory()
# output_directory = filedialog.askdirectory()
extension = ".cs"

file_comments = []
for root, dirs, files in os.walk(file_path):
    for file in files:
        if file.endswith(extension):
            full_path = os.path.join(root,file)
            comments = extract_comments(full_path)
            file_comments.append((full_path,comments))

print(file_comments)
