from pymongo import MongoClient
from fastapi import FastAPI, HTTPException
from fastapi import FastAPI

client = MongoClient('localhost', 27017)

db = client['course_db']
courses = db['courses']

app = FastAPI()


@app.get("/courses/")
async def get_courses(sort: str = "alphabetical", domain: str = None):
    query = {}
    if domain:
        query["domain"] = domain

    if sort == "alphabetical":
        cursor = courses.find(query).sort("name", 1)
    elif sort == "date":
        cursor = courses.find(query).sort("date", -1)
    elif sort == "rating":
        cursor = courses.find(query).sort("rating", -1)
    else:
        cursor = courses.find(query)
    courses_list = [course for course in cursor]
    for course in courses_list:
        if "_id" in course:
            course["_id"] = str(course["_id"])
    return {
        "courses": courses_list,
        "sort": sort,
        "domain": domain,
        "status": 200,
        "message": "Courses retrieved successfully"
    }


@app.get('/courses/course_name/')
async def get_course(course_name: str):
    course = courses.find_one({'name': course_name})
    if not course:
        raise HTTPException(status_code=404, detail='Course not found')
    chapters_list = course.get('chapters', [])
    for chapter in chapters_list:
        if 'ratings' in chapter:
            chapter['avg_rating'] = sum(chapter['ratings']) / len(chapter['ratings'])
    return {
        "course_name": course_name,
        "chapters": chapters_list,
        "status": 200,
        "message": "Course retrieved successfully"
    }


@app.get('/courses/course_with_chapter/')
async def get_chapter(course_name: str, chapter_name: str):
    course = courses.find_one({'name': course_name})
    if not course:
        raise HTTPException(status_code=404, detail='Course not found')
    chapter = next((c for c in course['chapters'] if c['name'] == chapter_name), None)
    if not chapter:
        raise HTTPException(status_code=404, detail='Chapter not found')
    if 'ratings' in chapter:
        chapter['avg_rating'] = sum(chapter['ratings']) / len(chapter['ratings'])
    return {
        "course_name": course_name,
        "chapter_name": chapter_name,
        "chapter_content": chapter.get('content', ''),
        "avg_rating": chapter.get('avg_rating', 0),
        "status": 200,
        "message": "Chapter retrieved successfully"
    }


@app.post('/courses/rate_chapter/')
async def rate_chapter(course_name: str, chapter_name: str, rating: int):
    course = courses.find_one({'name': course_name})
    if not course:
        raise HTTPException(status_code=404, detail='Course not found')
    chapter = next((c for c in course['chapters'] if c['name'] == chapter_name), None)
    if not chapter:
        raise HTTPException(status_code=404, detail='Chapter not found')
    if 'ratings' not in chapter:
        chapter['ratings'] = []
    chapter['ratings'].append(rating)
    courses.update_one({'name': course_name}, {'$set': {'chapters': course['chapters']}})
    return {
        "course_name": course_name,
        "chapter_name": chapter_name,
        "rating": rating,
        "status": 200,
        "message": "Chapter rating updated successfully"
    }
