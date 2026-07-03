# Scottish Law AI

An open source AI assistant that answers questions about Scottish law using real legislation from the Acts of the Scottish Parliament.

Built by Bluelineai as a free public resource for anyone who needs to understand Scottish law but cannot afford a solicitor or does not know where to start.

## What it does

You type a question in plain English and the AI searches through real Scottish legislation to find the most relevant sections and gives you an answer based on what the law actually says. It tells you which acts it used to find the answer so you can check the source yourself.

## What it does not do

This is not a replacement for a solicitor. It will tell you what the law says but it cannot give you legal advice for your specific situation. Always speak to a qualified Scottish solicitor for anything serious.

## Where the data comes from

All legislation comes from legislation.gov.uk published by The National Archives under the Open Government Licence v3.0. The data covers every Act of the Scottish Parliament from 1999 to 2026, which is 395 acts in total.

## How to run it yourself

You will need Python installed on your computer and Ollama running locally with the Phi3 model downloaded.

First install the required packages:

```
pip install streamlit chromadb sentence-transformers ollama
```

Then download the Phi3 model through Ollama:

```
ollama pull phi3
```

Then build the database from the legislation files:

```
python scripts/build_database.py
```

Then launch the app:

```
streamlit run app.py
```

Open your browser and go to localhost:8501 and you will see the chat interface.

## Project structure

```
scottish-law-ai/
  app.py                      the main chat interface
  scripts/
    download_legislation.py   downloads Scottish acts from legislation.gov.uk
    download_caselaw.py       downloads Scottish court judgments from BAILII
    build_database.py         indexes all the legal text into a searchable database
    test_search.py            checks the database is returning relevant results
    ask.py                    command line version of the question answering tool
  data/
    legislation/              Acts of the Scottish Parliament (1999 to 2026)
    caselaw/                  Scottish court judgments
  models/
    scottish_law_db/          the vector database that powers the search
```

## How it works

When you ask a question the system converts your question into a mathematical representation and searches the database for the chunks of legislation that are most similar. It then passes those chunks to the Phi3 language model along with your question and asks it to answer using only what the legislation says. This approach is called RAG, which stands for Retrieval Augmented Generation, and it means the AI is always grounded in real legal text rather than making things up.

## Coverage

Right now the database covers primary legislation only, which means Acts of the Scottish Parliament. We are working on adding Scottish Statutory Instruments and more court judgments from the Court of Session and the High Court of Justiciary.
Ultimate Goal:
Adding all of UK law and other jurisdictions like USA, Canada , Australia (mostly english speaking jurisdictions)

## Contributing

Contributions are very welcome. If you are a Scottish solicitor, legal academic, or just someone who cares about access to justice and wants to help improve the accuracy of the answers, please open an issue or get in touch.

## Licence

Code is released under the Apache License 2.0.

Legal data is Crown Copyright and sourced under the Open Government Licence v3.0 from legislation.gov.uk. Attribution is required if you reuse the data.

## Contact

info@bluelineai.com
