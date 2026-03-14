# Script Automation In a Box

I am Fabio Akita, known YouTuber at @Akitando channel. I published videos from the end of 2018 until the beginning of 2024. I also participated in many important Brazilian podcasts such as Flow and Inteligencia LTDA throughout 2024 and 2025. Prior to that I was the former organizer of Rubyconf Brasil from 2008 until 2016. I write at the blog akitaonrails.com since april of 2006 until now. I am also the co-founder of a boutique consultancy in Brazil especialized in team augmentation for USA dev teams called CodeMiner 42.

I am also very active in X.com as @akitaonrails.

Now, I want to try a new project: Script Automation in a Box for Apoia-se Extracted Data. This needs to be divided into multiple sub-projects here.

## 1. Extract and Transformation

I need to based on a CSV file, create a python local project that will read the CSV file and generate a YAML as output with the descriptions of the values inside of the CSV file based on some rules.

After openning the CSV file it contains the following columns:
- "ID","Apoiador","Email","Valor","Recompensa","Apoios Efetuados","Total Apoiado","Tipo","Status da Promessa","Visibilidade","Data da Última Mudança no Status da Promessa","CEP","Rua","Número","Complementos","Bairro","Cidade","UF","País","Endereço Completo". But we only need to use "ID", "Apoiador", "Email", "Valor", "Recompensa", "Apoios Efetuados", "Total Apoiado", "Status da Promessa", "Data da Última Mudança no Status da Promessa";
- The selected columns will give us the important data to deal with, so the next step will be to transform this data into a more useful format for analysis.


### 1.1 The Definition of the columns and samples

"ID" -> It's the unique identifier of the person helping with money. Sample value: ("2033E016D3DC40B", "84C036621550415)
"Apoiador" -> It's the name of the person helping with money. Sample value: ("Fabio Akita", "Marvin", "Rafa")
"Email" -> It's the email of the person helping with money. Sample value: ("fabio.akita@example.com", "someone@outlook.com")
"Valor" -> It's the value of the money he donated to the creator. Sample value: ("10.00", "20.00")
"Recompensa" -> It's the reward category in which the person helping with money is on. Sample value: ("5", "18", "60")
"Apoios Efetuados" -> It's the number of times the person helped with money. Sample value: ("1", "2")
"Total Apoiado" -> It's the total amount of money the person helped with money over time. Sample value: ("10.00", "20.00")
"Status da Promessa" -> It's the status of the promise, used to indentify which people are active or not in the donations. Sample value: ("Ativo", "Desativado", "Inadimplente", "Aguardando Confirmação");
"Data da Última Mudança no Status da Promessa" -> It's the date of the last change in the status of the promise. Sample value: ("2026-03-01 08:51", "2026-02-01 08:55")

### 1.2 What to do with the data

The data must be transformed in a way that we get a final output following the structure below:

```yaml
apoia-se:
  total_apoiadores: <int>
  total_pendente: <float>
  total_inadimplente: <float>
  total_recebido_mes_atual: <float>
  total_recebido_mes_anterior: <float>
  

  
  recompensas:
    <recompensa>: <int>
      apoiadores_com_status_ativo: <str>
      apoiadores_com_status_pendente: <str>
      apoiadores_com_status_inadimplente: <str>
      apoiadores_com_status_aguardando_confirmacao: <str>
  

```

### 1.3 How to build the YAML parameters
total_apoiadores must be the count(*) of total active donators. Active donators cab be identified by the column "Status da Promessa" == "Ativo"
total_pendente must be the count(*) of total donators with status "Aguardando Confirmação"
total_inadimplente must be the count(*) of total donators with status "Inadimplente"
total_recebido_mes_atual must be the sum of "Valor" of all donators with status "Ativo" and "Aguardando Confirmação" in the current month
total_recebido_mes_anterior must be the sum of "Valor" of all donators with status "Ativo" and "Aguardando Confirmação" in the previous month

recompensas must be a dictionary of all unique values in the column "Recompensa". And for each "Recompensa" category, the donators must be separated by status "Ativo", "Pendente", "Inadimplente", "Aguardando Confirmação" inside a string list comma separated using the "Apoiador" column value as Name, but only first and last name. If the donator doesn't have a last name, use the full name. The list must be sorted alphabetically.

### 1.4 Debugging
A metadata JSON must be created to debug scenarios. If the user wants to validate if two "Apoiadores" names "Rafa" are the same person, this can only be done by looking at the e-mail or id, so this JSON file will serve to validate this scenario.

## 6. Tech Stack

Use python with a proper venv to code and validate your tests;
Use polars or pandas to process and transform the data locally.
The project must by divided into modules to make it easier to test and validate each part of the project.
The project should pass unit tests to be valid.
The artifacts generated must be stored in a local folder inside the project called "artifacts" and each artifact should use as name a UUID. Example: "artifacts/<uuid>.yaml", "artifacts/<uuid>.json".
The Python Script must follow Python Engineering Best Practices, including typing, docstrings, and unit tests.
The project structure should be modular, don't put everything inside a single file and Dont repeat yourself.
The source data is inside "data/base-apoiadores-mf.csv"

## Final 

I need you to make a comprehensive plan (and write it down as PLAN.md) before coding anything, and make sure you ask me if I left anything unexplained or ambiguous.

This is a easy project, so don't make it more complicated than it is.