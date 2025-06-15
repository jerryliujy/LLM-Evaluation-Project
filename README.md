# 🎓 Database System Design - Final Project

> **Fudan University Database System Design Course Final Project**

📍 **Repository**: [LLM-Evaluation-Project](https://github.com/jerryliujy/LLM-Evaluation-Project)

---

## 🚀 Quick Setup

### 📋 Prerequisites

- **Python 3.9+** with virtual environment support
- **Node.js 16+** and npm
- **MySQL 8.0+** or compatible database
- Git

### 🗄️ Database Configuration

#### Option 1: Environment Variable (Recommended)

```bash
export DATABASE_URL="mysql+pymysql://username:password@localhost:3306/your_database"
```

#### Option 2: Direct Configuration

- Edit `backend/app/db/database.py` and set your `DATABASE_URL`

#### Initialize Database Schema

```sql
-- Run the complete schema
mysql -u username -p your_database < complete_database_schemas.sql
```

### 🔧 Backend Setup

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create and activate virtual environment
python -m venv venv

# Windows
.\venv\Scripts\activate
# macOS/Linux  
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the backend server
python run.py
```

**✅ Backend should now be running on `http://localhost:8000`**

### 🎨 Frontend Setup

> You should first config npm and node.js if they are not available on your local machine. For reference, see [npm](https://nodejs.cn/npm/cli/v8/configuring-npm/install/).

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install npm dependencies
npm install  

# 3. Start development server
npm run serve
```

**✅ Frontend should now be accessible at `http://localhost:8080`**

---

## 📂 Project Overview

| Directory | Description |
|-----------|-------------|
| `frontend/` | 🎨 Vue.js frontend application with UI components and service layers |
| `backend/` | ⚙️ FastAPI backend server with RESTful APIs |
| `backend/migrations/` | 📦 Database migration files (Alembic-based, currently unused) |
| `complete_database_schemas.sql` | 🗄️ **Production-ready SQL schema** for table creation |
| `gen_schemas.sql` | 📝 First version SQL queries (deprecated) |
| `ERgraph.jpg` | 📊 Entity-Relationship diagram (initial version) |
| `third_party/` | 🔗 External documentation and StackOverflow crawler (Thanks to [source](https://github.com/kkx9/dockerfile-llm.git)) |
| `test_data/` | 💾 Sample datasets - **production data located in `test_data/my_example_data/`** |

---

## 👥 User Guide

### 📊 For Dataset Managers

If you are a dataset manager, our platform can help you:

- ✅ **Build your own question pool**
- ✅ **Create your own dataset**  
- ✅ **Publicize your dataset**

#### 🎯 Getting Started

The most exciting part is absolutely **creating and publicizing your dataset**, but wait a minute. You should do some foundamental works in order to successfully create your dataset. For every question in the dataset, there must be some **raw questions** it refers to. This design guarantees transparency and credibility of the question. Therefore, we should construct our raw question pool first.

#### 📥 Data Import Methods

We enable **two ways** to load the raw Q&A pair into the pool:

1. **Manual Input**: Write records individually through the UI
2. **File Import**: Load from JSON file (**recommended** for efficiency)

> 💡 **Tip**: Check the loading-file page for the correct JSON format. Demo data available in `test_data/my_example_data/` folder.

Generally, the data importing function in our system is quite **straightforward and adaptable**. For nearly every data importing case in the system, we offer both manually importing method and file importing method.

#### 🏗️ Dataset Creation Process

1. **Initialize**: Give a name and description (optional)
2. **Create Q&A Pairs**: Manually create standard Q&A pairs or load from JSON
3. **Link References**: Specify raw questions that the standard question refers to
4. **Add Context**: Optionally refer to raw answers and expert answers

#### 📝 Question Types

- **📄 Text Questions**: Require explanations, answers with ordered scoring points
- **☑️ Choice Questions**: Single-choice format with definite answers

#### 🔄 Version Management (UNDER DEVELOPMENT)

We aim at building a **lightweight but integrated platform** that allows users to construct their databases smoothly, so we develop a **version management** that enables swift iteration.

**Key Benefits:**

- ⚡ **Swift iteration** through version editing interface
- 💾 **Memory efficient** - only stores modifications, not duplicates
- 🔄 **CRUD operations** on dataset versions
- 📊 **Version tracking** with detailed change logs (still pursuing...)

> This function is still underdevelopment and not that mature.

---

### 🎓 For Experts

Experts are welcomed to **label the raw questions** for dataset managers. By labelling I mean giving the **expert answer** to the question, which can provide guidance for finally creating standard answers.

#### 🔐 Access Control

- **Invite Code Required**: Get the invite code from the dataset manager to fully access their raw question pool
- **Guidance Role**: Expert answers serve as guidance and won't determine the standard answers

---

### 🤖 For LLM Users

Here users refer to those who want to **benchmark or evaluate LLMs** on datasets. We provide you with a **five-stage pipeline** for thorough evaluation:

#### 🚀 5-Stage Evaluation Pipeline

1. **⚙️ Config Parameters**: Configure LLM generation parameters  
   - Use your own API (currently supports `qwen-turbo`)
   - Add more models via SQL insert into `LLM` table

2. **💬 Config Prompts**: Configure generation prompts  
   - Different prompts for choice and text questions

3. **🎯 Generate Answers**: Generate answers using LLM

4. **📊 Evaluate Answers**: Score the LLM answers  
   - **Automatic**: Use LLM to score answers
   - **Manual**: Score answers yourself

5. **📈 Display Results**: View comprehensive evaluation results

#### 💾 State Persistence

> ⚠️ **Important**: We save results for each stage, meaning whenever you exit the pipeline you are **free to return** to the state before you exit. This adds great convenience since LLM evaluations always take long time.

#### 📥 Alternative Evaluation

Another way of evaluating LLM is to **download the dataset** and evaluate on your local machine. The downloaded data will always be in the **same consistent format**. Don't forget to record your evaluation results back in our system!

---

## ✨ System Features

1. **Formality**: we maintain every data in the dataset the same form. Although this setting prevents more flexible usage and diverse datasets as well, it provides a consistent interface where all you need to care is to find data, load data and evaluate your model instead of how to organize the data.
2. **Integrated**: our platform is available to data loading, dataset construction, data labeling and LLM evaluation, which cover several different aspects and allow users with different objectives to interact with each others on the platform.
3. **Convenience**: for some of the most important functions such as version management and LLM evaluation, our system packs the process for you, and you don't need to learn the underlying techniques to create dataset or evaluate LLM on your own.
