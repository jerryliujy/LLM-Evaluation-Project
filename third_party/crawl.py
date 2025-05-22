"""
This script is from https://github.com/kkx9/dockerfile-llm.git
I change its function to allow crawl multiple answers and additional information for single question.
"""

# 运行请前先运行
# mkdir "D:\AutomationProfile\edge"
# .\msedge.exe --remote-debugging-port=9222 --user-data-dir="D:\AutomationProfile\edge"

import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from datetime import datetime

def formalize_date(answer_date_raw):
    """answer_date_raw: 'Jan 1, 2023 at 12:00 AM' 
    """
    try:
        answer_date = datetime.strptime(answer_date_raw, "%b %d, %Y at %H:%M")
        # ISO 8601 format
        answer_date = answer_date.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        print(f"Could not parse date: {answer_date_raw}")
        answer_date = answer_date_raw  

    return answer_date

options = webdriver.EdgeOptions()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Edge(options=options)

try:
    # topic = "shell"
    topic = "dockerfile"
    pages = 5
    pagesize = 50
    position = 5
    answer_num = 7  # Number of answers to fetch per question
    
    output_dir = f"{topic}_questions"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    all_questions = []

    for page in range(1, pages + 1):
        for index in range(1, pagesize + 1):
            driver.get(f"https://stackoverflow.com/questions/tagged/{topic}?page={page}&sort=votes&pagesize={pagesize}")
            time.sleep(1)
            try:
                question_link = driver.find_element(By.XPATH, f"/html/body/div[{position}]/div[3]/div[1]/div[3]/div[{index}]/div[2]/h3/a")
                vote_number = driver.find_element(By.XPATH, f"/html/body/div[5]/div[3]/div[1]/div[3]/div[{index}]/div[1]/div[1]/span[1]").text
                view_number = driver.find_element(By.XPATH, f"/html/body/div[5]/div[3]/div[1]/div[3]/div[{index}]/div[1]/div[3]/span[1]").text
                # /html/body/div[5]/div[3]/div[1]/div[3]/div[1]/div[2]/div[2]/div[2]/div/div/a
                author = driver.find_element(By.XPATH, f"/html/body/div[5]/div[3]/div[1]/div[3]/div[{index}]/div[2]/div[2]/div[2]/div/div/a").text
                issued_at = driver.find_element(By.XPATH, f"/html/body/div[5]/div[3]/div[1]/div[3]/div[{index}]/div[2]/div[2]/div[2]/time/span").text
                issued_at = formalize_date(issued_at)
                
                tags = []
                tag_index = 1
                while True:
                    try:
                        tag_elements = driver.find_elements(By.XPATH, f"/html/body/div[5]/div[3]/div[1]/div[3]/div[{index}]/div[2]/div[2]/div[1]/ul/li[{tag_index}]/a")
                        if len(tag_elements) == 0:
                            break
                        for tag_element in tag_elements:
                            tag = tag_element.text
                            tags.append(tag)
                        tag_index += 1
                    except Exception as e:
                        print(f"Error when fetching tag {tag_index} for question: {e}")
                        break
                    
                question_url = question_link.get_attribute("href")
                print(f"Question URL: {question_url}")
                driver.get(question_url)
                time.sleep(1)

                question_title = driver.find_element(By.CSS_SELECTOR, "#question-header > h1 > a").text
                print(f"Index: {index}, Question Title: {question_title}, Vote Number: {vote_number}, View Number: {view_number}, Author: {author}, Issued At: {issued_at}")
                print(f"Tags: {tags}")

                # Collect up to `answer_num` answers
                answers = []
                upvote_counts = []
                answerers = []
                answer_dates = []
                for i in range(2, answer_num + 1):
                    try:
                        # /html/body/div[5]/div[3]/div[2]/div[1]/div[3]/div[3]/div[2]/div/div[2]/div[2]/div/div[3]/div/div[1]/div/span
                        answer = driver.find_element(By.XPATH, f"/html/body/div[5]/div[3]/div[2]/div[1]/div[3]/div[3]/div[{i}]/div/div[2]/div[1]").text
                        upvote_count = driver.find_element(By.XPATH, f"/html/body/div[5]/div[3]/div[2]/div[1]/div[3]/div[3]/div[{i}]/div/div[1]/div/div[2]").text
                        answer_by = driver.find_element(By.XPATH, f"/html/body/div[5]/div[3]/div[2]/div[1]/div[3]/div[3]/div[{i}]/div/div[2]/div[2]/div/div[3]/div/div[3]/a").text
                        answer_date = driver.find_element(By.XPATH, f"/html/body/div[5]/div[3]/div[2]/div[1]/div[3]/div[3]/div[{i}]/div/div[2]/div[2]/div/div[3]/div/div[1]/div/span").text
                        answer_date = formalize_date(answer_date)   
                        print(f"Answer: {i}, Upvotes: {upvote_count}, Answered by: {answer_by}, Answered at: {answer_date}")
                        if answer not in answers and len(answer) > 0:
                            answers.append(answer)
                        if len(upvote_count) > 0:
                            upvote_count = int(upvote_count.split()[0])
                            upvote_counts.append(upvote_count)
                        if len(answer_by) > 0:
                            answerers.append(answer_by)
                        if len(answer_date) > 0:
                            answer_dates.append(answer_date)
                            
                    except Exception as e:
                        print(f"Error when fetching answer {i} for question: {question_title}")
                        continue

                print(f"Collected {len(answers)} answers for question: {question_title}")
                if len(answers) == 0:
                    continue
                
                question_data = {
                    "title": question_title,
                    "url": question_url,
                    "votes": vote_number,
                    "views": view_number,
                    "author": author,
                    "issued_at": issued_at,
                    "tags": tags,
                    "answers": [
                        {"answer": answers[i], "upvotes": upvote_counts[i], "answered_by": answerers[i], "answered_at": answer_dates[i]}
                        for i in range(len(answers))
                    ]
                }
                
                all_questions.append(question_data)
            except Exception as e:
                print(f"Error processing question at index {index} on page {page}: {e}")
                continue
        print("page: ", page)
        
    output_file = os.path.join(output_dir, f"{topic}_all_questions.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_questions, f, indent=4)
    print(f"Saved all questions to {output_file}")
finally:
    driver.quit()