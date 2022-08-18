import os
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import filedialog
import subprocess
import uuid
import re
FILEBROWSER_PATH = os.path.join(os.getenv('WINDIR'), 'explorer.exe')
root = tk.Tk()
root.withdraw()

md_new_line = '\n'
xmltag_regex = re.compile("(<.[^(><.)]+>)")


class XMLComment:
    def __init__(self, comment, statement, new_line_delimitter):
        self.new_line_delimitter = new_line_delimitter

        self.comment = comment
        self.parsed_comment = None
        self.summary_comment = None
        self.returns_comment = None
        self.param_comments = []
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

        self.parsed_comment = self.comment.split('///')

        # remove first index as it is always empty string
        self.parsed_comment = self.parsed_comment[1:]

        # strip
        self.parsed_comment = list(
            map(lambda line: line.strip(), self.parsed_comment))

        # handle new lines
        for i in range(1, len(self.parsed_comment)):
            # if previous line is not an xml tag
            if re.match(xmltag_regex, self.parsed_comment[i - 1]) is None:
                self.parsed_comment[i] += self.new_line_delimitter

        self.parsed_comment = ''.join(self.parsed_comment)  # markdown new line
        self.parsed_comment = BeautifulSoup(self.parsed_comment)

        self.summary_comment = self.parsed_comment.summary.text if self.parsed_comment.summary is not None else ''

        self.returns_comment = self.parsed_comment.returns.text if self.parsed_comment.returns is not None else ''

        for comment in self.parsed_comment.find_all('param'):
            self.param_comments.append(f'**{comment["name"]}**: {str(comment.next)}')
        self.param_comments = ", ".join(self.param_comments)

    def get_markdown():
        pass


class XMLComment_Interface(XMLComment):
    def __init__(self, comment, statement):
        super().__init__(comment, statement, '. ')

    def parse_statement(self):
        if self.split_statement[0] == 'interface':
            self.split_statement.insert(0, 'private')
        self.title = self.split_statement[2]
        self.encapsulation = self.split_statement[0]

    def get_markdown(self):
        return f"""|{self.title}|{self.summary_comment}|"""


class XMLComment_Class(XMLComment):
    def __init__(self, comment, statement, new_line_delimitter='\n'):
        super().__init__(comment, statement, new_line_delimitter)

    def parse_statement(self):
        if self.split_statement[0] == 'class':
            self.split_statement.insert(0, 'private')
        self.modifier = self.split_statement[1] if self.split_statement[1] == 'abstract' else None
        self.title = self.split_statement[2 if self.modifier is None else 3]
        self.encapsulation = self.split_statement[0]
        try:
            self.super_class = self.split_statement[self.split_statement.index(
                ":") + 1]
        except ValueError:
            self.super_class = None

    def get_markdown(self):
        return f"""# {self.title}
*class/ Inherits from:{self.super_class}*
        
## Description
{self.summary_comment}"""


class XMLComment_SubClass(XMLComment_Class):
    def __init__(self, comment, statement):
        super().__init__(comment, statement, new_line_delimitter='. ')

    def get_markdown(self):
        return f"""|{self.title}|{self.summary_comment}|"""


class XMLComment_Enum(XMLComment):
    def __init__(self, comment, statement):
        super().__init__(comment, statement, '. ')

    def parse_statement(self):
        if self.split_statement[0] == 'enum':
            self.split_statement.insert(0, 'private')
        self.title = self.split_statement[2]
        self.encapsulation = self.split_statement[0]

    def get_markdown(self):
        return f"""|{self.title}|{self.summary_comment}|"""


class XMLComment_Function(XMLComment):
    def __init__(self, comment, statement):
        super().__init__(comment, statement, '. ')

    def parse_statement(self):
        if self.split_statement[0] != 'private' and self.split_statement[0] != 'public' and self.split_statement[0] != 'protected':
            self.split_statement.insert(0, 'private')
        self.modifier = self.split_statement[1] if self.split_statement[1] in [
            'abstract', 'override', 'virtual'] else None
        self.title = self.split_statement[2 if self.modifier is None else 3].split('(')[
            0]
        self.encapsulation = self.split_statement[0]
        self.parameters = self.statement.split('(')[1].split(')')[0].split(',')
        self.parameters = list(
            map(lambda param: param.strip(), self.parameters))
        self.parameters = list(
            filter(lambda param: param != '', self.parameters))
        self.type = self.split_statement[1]

    def get_markdown(self):
        return f"""|{self.title}|{self.summary_comment}|{self.returns_comment}|{self.param_comments}|{self.type}|"""


class XMLComment_Variable(XMLComment):
    def __init__(self, comment, statement):
        super().__init__(comment, statement, '. ')

    def parse_statement(self):
        if self.split_statement[0] != 'private' and self.split_statement[0] != 'public' and self.split_statement[0] != 'protected':
            self.split_statement.insert(0, 'private')
        self.encapsulation = self.split_statement[0]
        self.title = self.split_statement[2]
        self.type = self.split_statement[1]

    def get_markdown(self):
        return f"""|{self.title}|{self.summary_comment}|{self.type}|"""


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


class File_Comments:
    def __init__(self, file, file_path):
        self.file = file
        self.file_path = file_path

        self.comments = []
        self.main_class_comment = None
        self.get_comments()

        self.markdown = None
        self.get_markdown()

    def get_markdown(self):
        if self.main_class_comment is None:
            return

        subclasses = list(filter(lambda c: isinstance(
            c, XMLComment_SubClass), self.comments))
        interfaces = list(filter(lambda c: isinstance(
            c, XMLComment_Interface), self.comments))
        enums = list(filter(lambda c: isinstance(
            c, XMLComment_Enum), self.comments))
        properties = list(filter(lambda c: isinstance(
            c, XMLComment_Variable), self.comments))
        methods = list(filter(lambda c: isinstance(
            c, XMLComment_Function), self.comments))

        self.markdown = ""

        self.markdown += f"""{self.main_class_comment.get_markdown()}"""

        if len(subclasses) > 0:
            self.markdown += f"""
## Subclasses
|Subclass|Description|
|-----------|-----------|
{md_new_line.join(map(lambda c: c.get_markdown(),subclasses))}
            """

        if len(interfaces) > 0:
            self.markdown += f"""
## Interfaces
|Interface|Description|
|-----------|-----------|
{md_new_line.join(map(lambda c: c.get_markdown(),interfaces))}
            """

        if len(enums) > 0:
            self.markdown += f"""
## Enums
|Enum|Description|
|-----------|-----------|
{md_new_line.join(map(lambda c: c.get_markdown(),enums))}
            """

        if len(properties) > 0:
            self.markdown += f"""
## Public Properties
|Property|Description|Type|
|-----------|-----------|-----------|
{md_new_line.join(map(lambda c: c.get_markdown(),properties))}
            """

        if len(methods) > 0:
            self.markdown += f"""
## Public Methods
|Method|Description|Returns|Parameters|Type|
|-----------|-----------|-----------|-----------|-----------|
{md_new_line.join(map(lambda c: c.get_markdown(),methods))}
            """

    def get_comments(self):
        self.comments = []
        with open(self.file_path) as f:
            current_comment = None
            for line in f:
                line = line.strip()
                # comment detected
                if line.startswith("///"):
                    if current_comment is None:
                        if '<' in line and '>' in line:
                            current_comment = line
                    else:
                        current_comment += line
                else:
                    # comment finished
                    if current_comment is not None:
                        if line == '':
                            continue
                        if line.startswith('['):
                            continue  # ignore serialization etc.

                        # determine which type of parser to use for the property
                        prop_type = determine_prop_type(line)

                        # handle class within classes
                        if prop_type == XMLComment_Class and self.main_class_comment is not None:
                            prop_type = XMLComment_SubClass

                        # create the comment object
                        prop_comment = prop_type(current_comment, line)

                        # set the main class comment or add class comment to buff
                        if prop_type == XMLComment_Class:
                            self.main_class_comment = prop_comment
                        else:
                            self.comments.append(prop_comment)
                        current_comment = None

class Index:
    def __init__(self,file_comments):
        self.files_comments = file_comments
        self.markdown = None
        self.get_markdown()

    def get_markdown(self):
        links = map(lambda file_comment: f"* [{file_comment.file}](./{file_comment.file}) *{file_comment.file_path}*",self.files_comments)
        self.markdown = f"""## Scripts
{md_new_line.join(links)}
        """

# get the path for where code files exist
file_path = filedialog.askdirectory()
extension = ".cs"

# parse and extract the comments
file_comments = []
for root, dirs, files in os.walk(file_path):
    for file in files:
        if file.endswith(extension):
            full_path = os.path.join(root, file)
            file_comments.append(File_Comments(file, full_path))

# get the output directory
folder_name = uuid.uuid4()
output_directory = os.path.join(os.getcwd(), "exports", str(folder_name))

# ensure output directory exists
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# write the files
for file_comment in file_comments:
    if file_comment.markdown is not None:
        with open(os.path.join(output_directory, file_comment.file + ".md"), "w") as file:
            file.write(file_comment.markdown)
            file.close()

# save the index file
index = Index(file_comments)
if index.markdown is not None:
    with open(os.path.join(output_directory, "Developer-Docs.md"), "w") as file:
        file.write(index.markdown)
        file.close()

# open the export directory
if os.path.isdir(output_directory):
    subprocess.run([FILEBROWSER_PATH, output_directory])
