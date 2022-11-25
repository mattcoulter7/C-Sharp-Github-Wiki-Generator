# C-Sharp-Github-Wiki-Generator
Creates a Github Wiki by extracting C# Visual Studio XML Documentation

## Required Code Format
`///<summary>Summary of something...</summary>`

## Dependencies
1. bs4
2. tkinter

## How to run
1. Run `python main.py`
2. Select the folder directory containing all the c# scripts you want to create documentation for. (scripts from subfolders are also included :))
3. The new window will popup showing the markdown export. You can copy these files into you Github Wiki Repository. 
4. There is a file called `Developer-Docs.md`, this is a markdown file containing links to all of the generated markdown files. This is ideal to use if you have a custom HTML Sidebar

## Screenshots
![image](https://user-images.githubusercontent.com/53892067/203908982-51bf9fc3-a724-4e43-b8a0-1717c12b88a7.png)
