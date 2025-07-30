import asyncio
import os
import json
from typing import List
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel, Runner, function_tool, set_tracing_disabled,Runner
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

BASE_URL = os.getenv("BASE_URL") 
API_KEY = os.getenv("API_KEY") 
MODEL_NAME = os.getenv("MODEL_NAME") 

if not BASE_URL or not API_KEY or not MODEL_NAME:
    raise ValueError(
        "Please set BASE_URL, API_KEY, and MODEL_NAME."
    )

client = AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY)
set_tracing_disabled(disabled=True)

# --- Models for structured outputs ---
class SkillsForTargetJob(BaseModel):
    """Represents the skills required for a target job."""
    missing_skills: List[str]
    target_job: str = Field(description="The job title for which the skills are being analyzed.")
class JobListing(BaseModel):
    """Represents a job listing with its details."""
    title: str
    company: str
    location: str
    required_skills: List[str]
# class CourseRecommendation(BaseModel):
#     courses: List[dict]


class Course(BaseModel):
    """Represents a course with its details."""
    title: str
    platform: str
    link: str

class CourseRecommendations(BaseModel):
    """The final list of recommended courses for the user."""
    courses: List[Course] = Field(description="A list of recommended courses.")


# A. Skill data: Maps job roles to a list of required skills.
JOB_SKILLS_DB = {
    "data scientist": ["Python", "SQL", "Machine Learning", "Statistics", "Pandas", "Communication"],
    "data analyst": ["SQL", "Excel", "Tableau", "R", "Statistics", "Communication"],
    "software engineer": ["Python", "Java", "Data Structures", "Algorithms", "Git", "System Design"],
    "product manager": ["Product Strategy", "UX Design", "Agile Methodologies", "Market Research", "Communication"],
    "ux designer": ["Figma", "User Research", "Wireframing", "Prototyping", "Usability Testing"]
}

# B. Job listings: A list of dummy job openings.
JOB_LISTINGS_DB = [
    {
        "title": "Data Scientist", "company": "Innovate AI", "location": "Remote",
        "skills": ["Python", "Machine Learning", "Statistics"]
    },
    {
        "title": "Senior Data Scientist", "company": "Future Corp", "location": "New York, NY",
        "skills": ["Python", "SQL", "Machine Learning", "Pandas", "System Design"]
    },
    {
        "title": "Data Analyst", "company": "Data Insights LLC", "location": "Austin, TX",
        "skills": ["SQL", "Tableau", "Excel", "Communication"]
    },
    {
        "title": "Software Engineer (Backend)", "company": "CodeCrafters", "location": "San Francisco, CA",
        "skills": ["Python", "Java", "System Design", "Git"]
    },
    {
        "title": "Product Manager", "company": "NextGen Products", "location": "Remote",
        "skills": ["Product Strategy", "Agile Methodologies", "Market Research"]
    }
]

# C. Course catalog: Maps skills to recommended courses.
COURSE_CATALOG_DB = {
    "python": [{"title": "Python for Everybody", "platform": "Coursera", "link": "https://www.coursera.org/specializations/python"}],
    "sql": [{"title": "The Complete SQL Bootcamp", "platform": "Udemy", "link": "https://www.udemy.com/course/the-complete-sql-bootcamp/"}],
    "machine learning": [{"title": "Machine Learning by Andrew Ng", "platform": "Coursera", "link": "https://www.coursera.org/learn/machine-learning"}],
    "statistics": [{"title": "Intro to Statistics", "platform": "Udacity", "link": "https://www.udacity.com/course/intro-to-statistics--st101"}],
    "pandas": [{"title": "Data Analysis with Python and Pandas", "platform": "Udemy", "link": "https://www.udemy.com/course/python-for-data-science-and-machine-learning-bootcamp/"}],
    "java": [{"title": "Java Programming Masterclass", "platform": "Udemy", "link": "https://www.udemy.com/course/java-the-complete-java-developer-course/"}],
    "product strategy": [{"title": "Become a Product Manager", "platform": "Udacity", "link": "https://www.udacity.com/course/product-manager-nanodegree--nd036"}]
}

# ------------------------------------------------------------------------------
# Tools used by Specialist Agents
# ------------------------------------------------------------------------------
@function_tool
def get_missing_skills(user_skills, target_job):
    """Identifies the skill gap for a target job."""
    target_job = target_job.lower()
    if target_job not in JOB_SKILLS_DB:
        return {"error": f"Sorry, We don't have any information about the job title '{target_job}'."}
    
    required_skills = set(skill.lower() for skill in JOB_SKILLS_DB[target_job])
    user_skills_set = set(skill.lower() for skill in user_skills)
    
    missing_skills = list(required_skills - user_skills_set)
    return {"target_job": target_job, "missing_skills": missing_skills}

@function_tool
def find_jobs(user_skills, location=None):
    """Finds jobs based on user skills and optional location."""
    user_skills_set = set(skill.lower() for skill in user_skills)
    matching_jobs = []
    
    for job in JOB_LISTINGS_DB:
        job_skills_set = set(skill.lower() for skill in job["skills"])
        
        # Find jobs where at least one user skill matches
        if user_skills_set.intersection(job_skills_set):
            if location is not None:
                if location and location.lower() not in job["location"].lower():
                    continue # Skip if location doesn't match
            matching_jobs.append(job)
            
    return {"jobs_found": matching_jobs}

@function_tool
def recommend_courses(user_skills):
    """Recommends courses for a list of skills."""
    recommendations = {}
    for skill in user_skills:
        skill_lower = skill.lower()
        if skill_lower in COURSE_CATALOG_DB:
            recommendations[skill] = COURSE_CATALOG_DB[skill_lower]
            
    #return {"course_recommendations": recommendations}
    return json.dumps(recommendations)


# ==============================================================================
# 🤖 2. AGENT DEFINITIONS
# ==============================================================================

job_search_agent = Agent(
    name="Job Search Specialist",
    handoff_description="Finds job listings based on user skills and location.",
    instructions="""
    This agent helps users find job opportunities that match their skills and preferred location.

    Use the `find_jobs` tool to search for jobs based on user skills and location.
    Example: `find_jobs(user_skills=["Python", "SQL"], location="New York")`

    If user doesn't provide a location, search for jobs without location filtering.

    Format your response in a clear, organized way with job details and skills.
    """,
    model=OpenAIChatCompletionsModel(
        openai_client=client,
        model=MODEL_NAME
    ),
    tools=[find_jobs],
    output_type=JobListing
)


course_recommendation_agent = Agent(
    name="Course Recommender Specialist",
    handoff_description="Recommends courses to fill skill gaps.",
    instructions="""
    This agent helps users find courses to improve their skills for a specific job role.

    Use the `recommend_courses` tool to suggest courses based on missing skills.
    Example: `recommend_courses(user_skills=["Python", "SQL"])`

    Always explain the reasoning behind your recommendations.

    Format your response in a clear, organized way with course details.
    """,
    model=OpenAIChatCompletionsModel(
        openai_client=client,
        model=MODEL_NAME
    ),
    tools=[recommend_courses],
    output_type=CourseRecommendations
)




skill_gap_agent = Agent(
    name="Skill Gap Specialist",
    handoff_description="Identifies missing skills for a target job.",
    instructions="""    
    This agent helps users understand what skills they need to acquire for a specific job role.
    
    Use the `get_missing_skills` tool to find out which skills are missing for a given job title.
    Example: `get_missing_skills(user_skills=["Python", "SQL"], target_job="Data Scientist")`

    Always explain the reasoning behind your recommendations.

    Format your response in a clear, organized way with target job details and skills.
    """,
    model=OpenAIChatCompletionsModel(
        openai_client=client,
        model=MODEL_NAME
    ),
    tools=[get_missing_skills],
    #handoffs=[job_search_agent, course_recommendation_agent],
    output_type=SkillsForTargetJob
)


conversation_agent = Agent(
    name="Career Mate",
    handoff_description="Conversational agent. Provides career advice and connects to specialists.",
    instructions="""
    You are a career development assistant. Your role is to identify the right specialist agent to hand off to.
    You can hand off to specialist agents for specific tasks like Skill Gap Specialist, Job Search Specialist or Course Recommender Specialist.
    
    Don't try to answer the user's question directly. Instead, analyze the query and determine which specialist agent is best suited to handle it.
    """,
    model=OpenAIChatCompletionsModel(
        openai_client=client,
        model=MODEL_NAME
    ),
    #tools=[get_missing_skills, find_jobs, recommend_courses],
    #output_type=Union[SkillsForTargetJob, JobListing, CourseRecommendation]
    #output_type=CareerAdvice
    handoffs=[skill_gap_agent,job_search_agent, course_recommendation_agent],
)

async def main():

    # Example queries to test different aspects of the system
    queries = [
        "I want to become a Data Scientist. What skills do I need?",
        "I have skills in Python and SQL. What jobs can I apply for?",
        "I am looking for jobs in New York that require Python and SQL skills.",
        "I want to improve my skills in Machine Learning. What courses do you recommend?",
    ]
    
    for query in queries:
        print("\n" + "="*50)
        print(f"QUERY: {query}")
        result = await Runner.run(conversation_agent, query)
        #print(f"RESULT: {result}")

        if hasattr(result.final_output, "missing_skills"):  # Flight recommendation
            #print("********SKILL GAP ANALYSIS************")
            missing_skills = result.final_output            
            print(f"MISSING SKILLS: {missing_skills.missing_skills}")
        elif hasattr(result.final_output, "required_skills"):  # Job search
            #print("*******JOB SEARCH RESULTS*********")                
            jobs = result.final_output
            print(f"{jobs}")
        elif hasattr(result.final_output, "courses"):  # Course recommendation
            #print("**********COURSE RECOMMENDATIONS***********")
            courses = result.final_output.courses
            print(f"RECOMMENDED COURSES: {courses}")
        else:
            print("Sorry, I can't assist with that.")



if __name__ == "__main__":
    #print(get_jobs(user_skills=["Python", "SQL"]))
    asyncio.run(main())
