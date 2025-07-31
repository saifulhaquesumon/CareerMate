********************** CareerMate ***********************

 🧠 Project: Multi-Agent Career Advisor – “CareerMate”

 This script implements a multi-agent system to guide users in their career paths.
 It includes a main Conversation Agent that routes tasks to specialized agents for
 skill gap analysis, job searching, and course recommendations.

project structure
- career_mate_agent.py --Run this file, call main function

This program written in  VSCode.
## Setup

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your OpenAI API key:


API_KEY= "your api key" 
BASE_URL= "https://models.github.ai/inference"
MODEL_NAME= "openai/gpt-4.1-nano"

run the career_mate_agent.py file

==================================================
QUERY: I want to become a Data Scientist. What skills do I need?
MISSING SKILLS: ['Python programming', 'R programming', 'Data Wrangling and Cleaning', 'Statistical Analysis', 'Machine Learning', 'Data Visualization', 'Big 
Data Tools (e.g., Hadoop, Spark)', 'SQL and Databases', 'Deep Learning Basics', 'Data Storytelling and Communication', 'Model Deployment', 'Knowledge of Cloud Platforms (e.g., AWS, Azure, GCP)', 'Business Domain Knowledge', 'Version Control (e.g., Git)']

==================================================
QUERY: I have skills in Python and SQL. What jobs can I apply for?
title='Senior Data Scientist' company='Future Corp' location='New York, NY' required_skills=['Python', 'SQL', 'Machine Learning', 'Pandas', 'System Design']  

==================================================
QUERY: I am looking for jobs in New York that require Python and SQL skills.   
title='Senior Data Scientist' company='Future Corp' location='New York, NY' required_skills=['Python', 'SQL', 'Machine Learning', 'Pandas', 'System Design']  

==================================================
QUERY: I want to improve my skills in Machine Learning. What courses do you recommend?
RECOMMENDED COURSES: [Course(title='Machine Learning by Andrew Ng', platform='Coursera', link='https://www.coursera.org/learn/machine-learning')]

==================================================
