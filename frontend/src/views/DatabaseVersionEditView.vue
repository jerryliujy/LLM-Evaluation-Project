<template>
  <div class="version-edit-container">
    <div class="header">
      <div class="header-left">
        <button @click="goBackToDatabase" class="back-btn">
          ← 返回数据库管理
        </button>
        <div class="title-section">
          <h2>编辑版本</h2>
          <p class="subtitle" v-if="currentDataset && currentVersion">
            数据库: {{ currentDataset.name }} - 版本 #{{ currentVersion.id }}
          </p>
          <p class="version-description" v-if="currentVersion">
            {{ currentVersion.description }}
          </p>
        </div>
      </div>      <div class="header-actions">
        <button @click="previewChanges" class="preview-btn" :disabled="!hasChanges">
          📋 预览更改
        </button>
        <button @click="saveVersion" class="save-version-btn" :disabled="saving || !hasChanges">
          {{ saving ? "创建版本中..." : "创建新版本" }}
        </button>
      </div>
    </div>

    <!-- 编辑界面 -->
    <div class="edit-interface">
      <!-- 工具栏 -->
      <div class="toolbar">
        <div class="toolbar-left">
          <div class="stats">
            <span class="stat-item">
              <span class="stat-label">总计:</span>
              <span class="stat-value">{{ stdQuestions.length }}</span>
            </span>
            <span class="stat-item">
              <span class="stat-label">已修改:</span>
              <span class="stat-value modified">{{ modifiedItems.length }}</span>
            </span>
          </div>
        </div>
        <div class="toolbar-right">
          <button @click="showImportModal = true" class="import-btn">
            📁 导入数据
          </button>
          <button @click="goToManualCreation" class="create-btn">
            ➕ 手动创建
          </button>
        </div>
      </div>

      <!-- 标准问答对列表 -->
      <div class="qa-list">
        <div 
          v-for="question in stdQuestions" 
          :key="question.id"
          class="qa-item"
          :class="{ 'modified': modifiedItems.includes(question.id) }"
        >
          <div class="qa-header">
            <div class="qa-info">
              <span class="qa-id">#{{ question.id }}</span>
              <span v-if="modifiedItems.includes(question.id)" class="modified-badge">已修改</span>
            </div>
            <div class="qa-actions">
              <button @click="editQuestion(question)" class="edit-btn">
                ✏️ 编辑
              </button>
              <button @click="deleteQuestion(question.id)" class="delete-btn">
                🗑️ 删除
              </button>
            </div>
          </div>

          <div class="qa-content">
            <div class="question-section">
              <h4>问题</h4>
              <div class="question-text">{{ question.body }}</div>
              <div class="question-meta">
                <span class="question-type">类型: {{ question.question_type === 'text' ? '文本题' : '选择题' }}</span>
                <div class="tags" v-if="question.tags && question.tags.length > 0">
                  <span v-for="tag in question.tags" :key="tag" class="tag">{{ tag }}</span>
                </div>
              </div>
            </div>

            <div class="answers-section" v-if="question.std_answers && question.std_answers.length > 0">
              <h4>标准答案</h4>
              <div v-for="answer in question.std_answers" :key="answer.id" class="answer-item">
                <div class="answer-text">{{ answer.answer }}</div>
                <div class="answer-meta">
                  <span v-if="answer.answered_by">回答者: {{ answer.answered_by }}</span>
                  <span v-if="answer.scoring_points && answer.scoring_points.length > 0">
                    得分点: {{ answer.scoring_points.length }}个
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 编辑弹窗 -->
    <div v-if="showEditModal" class="modal-overlay" @click="closeEditModal">
      <div class="edit-modal" @click.stop>
        <div class="modal-header">
          <h3>编辑标准问答对</h3>
          <button @click="closeEditModal" class="close-btn">×</button>
        </div>
        <div class="modal-content">
          <form @submit.prevent="saveEdit" class="edit-form">
            <!-- 问题编辑 -->
            <div class="form-group">
              <label for="edit-question">问题内容：</label>
              <textarea
                id="edit-question"
                v-model="editForm.body"
                rows="3"
                class="form-control"
                required
              ></textarea>
            </div>

            <div class="form-group">
              <label for="edit-question-type">问题类型：</label>
              <select id="edit-question-type" v-model="editForm.question_type" class="form-control">
                <option value="text">文本题</option>
                <option value="choice">选择题</option>
              </select>
            </div>

            <!-- 标签编辑 -->
            <div class="form-group">
              <label>标签：</label>
              <div class="tags-editor">
                <div class="current-tags">
                  <span v-for="(tag, index) in editForm.tags" :key="index" class="tag-item">
                    {{ tag }}
                    <button type="button" @click="removeTag(index)" class="remove-tag-btn">×</button>
                  </span>
                </div>
                <div class="add-tag">
                  <input 
                    v-model="newTag"
                    type="text" 
                    placeholder="输入新标签后按回车添加"
                    @keyup.enter="addTag"
                    class="form-control"
                  />
                  <button type="button" @click="addTag" class="add-tag-btn" :disabled="!newTag.trim()">
                    添加
                  </button>
                </div>
              </div>
            </div>

            <!-- 答案编辑 -->
            <div class="form-group">
              <label>标准答案：</label>
              <div class="answers-editor">
                <div v-for="(answer, index) in editForm.std_answers" :key="index" class="answer-edit-item">
                  <div class="answer-header">
                    <label>答案 {{ index + 1 }}:</label>
                    <button type="button" @click="removeAnswer(index)" class="remove-answer-btn">删除</button>
                  </div>
                  <textarea
                    v-model="answer.answer"
                    placeholder="输入答案内容..."
                    rows="3"
                    class="form-control"
                  ></textarea>
                  <div class="answer-meta-edit">
                    <input
                      v-model="answer.answered_by"
                      type="text"
                      placeholder="回答者"
                      class="form-control small"
                    />
                  </div>
                  
                  <!-- 得分点编辑 -->
                  <div class="scoring-points-section">
                    <label>得分点：</label>
                    <div class="scoring-points-list">
                      <div v-for="(point, pointIndex) in answer.scoring_points" :key="pointIndex" class="scoring-point-item">
                        <textarea
                          v-model="point.answer"
                          placeholder="输入得分点内容..."
                          rows="2"
                          class="form-control"
                        ></textarea>
                        <div class="point-controls">
                          <input
                            v-model.number="point.point_order"
                            type="number"
                            min="1"
                            placeholder="顺序"
                            class="form-control small"
                          />
                          <button type="button" @click="removeScoringPoint(index, pointIndex)" class="remove-point-btn">删除</button>
                        </div>
                      </div>
                    </div>
                    <button type="button" @click="addScoringPoint(index)" class="add-point-btn">添加得分点</button>
                  </div>
                </div>
                <button type="button" @click="addAnswer" class="add-answer-btn">添加答案</button>
              </div>
            </div>

            <div class="form-actions">
              <button type="button" @click="closeEditModal" class="cancel-btn">取消</button>
              <button type="submit" class="save-btn" :disabled="editSaving">
                {{ editSaving ? "保存中..." : "保存" }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- 创建问答对弹窗 -->
    <div v-if="showCreateModal" class="modal-overlay" @click="closeCreateModal">
      <div class="create-modal" @click.stop>
        <div class="modal-header">
          <h3>创建新的标准问答对</h3>
          <button @click="closeCreateModal" class="close-btn">×</button>
        </div>
        <div class="modal-content">
          <form @submit.prevent="createNewQA" class="create-form">
            <div class="form-group">
              <label for="new-question">问题内容：</label>
              <textarea
                id="new-question"
                v-model="createForm.body"
                rows="3"
                class="form-control"
                required
              ></textarea>
            </div>

            <div class="form-group">
              <label for="new-question-type">问题类型：</label>
              <select id="new-question-type" v-model="createForm.question_type" class="form-control">
                <option value="text">文本题</option>
                <option value="choice">选择题</option>
              </select>
            </div>

            <div class="form-group">
              <label for="new-answer">答案内容：</label>
              <textarea
                id="new-answer"
                v-model="createForm.answer"
                rows="3"
                class="form-control"
                required
              ></textarea>
            </div>

            <div class="form-actions">
              <button type="button" @click="closeCreateModal" class="cancel-btn">取消</button>
              <button type="submit" class="save-btn" :disabled="createSaving">
                {{ createSaving ? "创建中..." : "创建" }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- 导入数据弹窗 -->
    <div v-if="showImportModal" class="modal-overlay" @click="closeImportModal">
      <div class="import-modal" @click.stop>
        <div class="modal-header">
          <h3>导入标准问答数据</h3>
          <button @click="closeImportModal" class="close-btn">×</button>
        </div>
        <div class="modal-content">
          <!-- 文件上传区域 -->
          <div 
            class="upload-area" 
            @drop="handleDrop" 
            @dragover.prevent 
            @dragenter.prevent
            :class="{ 'drag-over': isDragOver }"
          >
            <div class="upload-content">
              <div class="upload-icon">📁</div>
              <p>拖拽JSON文件到此处，或点击选择文件</p>
              <input
                ref="fileInput"
                type="file"
                accept=".json"
                @change="handleFileSelect"
                style="display: none"
              />
              <button @click="fileInput?.click()" class="select-file-btn">选择文件</button>
            </div>
          </div>          <!-- 预览和导入 -->
          <div v-if="importPreviewData.length > 0" class="import-preview">
            <h4>数据预览</h4>
            <p>共 {{ importPreviewData.length }} 条记录</p>
            
            <!-- 预览表格 -->
            <div class="preview-table-container">
              <table class="preview-table">
                <thead>
                  <tr>
                    <th>问题内容</th>
                    <th>答案内容</th>
                    <th>问题类型</th>
                    <th>标签</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, index) in importPreviewData.slice(0, 5)" :key="index">
                    <td class="preview-cell">{{ item.body || '未提供' }}</td>
                    <td class="preview-cell">{{ item.answer || '未提供' }}</td>
                    <td class="preview-cell">{{ item.question_type === 'text' ? '文本题' : '选择题' }}</td>
                    <td class="preview-cell">
                      <span v-if="item.tags && item.tags.length > 0" class="preview-tags">
                        <span v-for="tag in item.tags" :key="tag" class="preview-tag">{{ tag }}</span>
                      </span>
                      <span v-else>无标签</span>
                    </td>
                  </tr>
                </tbody>
              </table>
              <p v-if="importPreviewData.length > 5" class="preview-note">
                显示前5条记录，总共{{ importPreviewData.length }}条
              </p>
            </div>
            
            <div class="preview-actions">
              <button @click="clearImportPreview" class="clear-btn">清除</button>
              <button @click="confirmImport" class="import-confirm-btn" :disabled="importing">
                {{ importing ? "导入中..." : "确认导入" }}
              </button>
            </div>
          </div>

          <div v-if="importError" class="error-message">
            {{ importError }}
          </div>
        </div>
      </div>
    </div>

    <!-- 消息提示 -->
    <div v-if="message" class="message" :class="messageType">
      {{ message }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { datasetService } from '@/services/datasetService';
import { versionService } from '@/services/versionService';
import { datasetVersionWorkService } from '@/services/datasetVersionWorkService';

// 路由
const route = useRoute();
const router = useRouter();

// 响应式数据
const datasetId = computed(() => route.params.datasetId as string);
const versionId = computed(() => route.params.versionId as string);
const currentDataset = ref<any>(null);
const currentVersion = ref<any>(null);
const versionWorkId = ref<number | null>(null); // 版本工作ID

// 编辑相关
const stdQuestions = ref<any[]>([]);
const modifiedItems = ref<number[]>([]);
const saving = ref(false);
const hasChanges = computed(() => modifiedItems.value.length > 0);
const showEditModal = ref(false);
const showCreateModal = ref(false);
const showImportModal = ref(false);

// 编辑表单
const editForm = ref<any>({});
const editSaving = ref(false);
const selectedQuestion = ref<any>(null);
const newTag = ref('');

// 创建表单
const createForm = ref({
  body: '',
  question_type: 'text',
  answer: ''
});
const createSaving = ref(false);

// 导入相关
const fileInput = ref<HTMLInputElement>();
const importPreviewData = ref<any[]>([]);
const isDragOver = ref(false);
const importing = ref(false);
const importError = ref('');

// 消息提示
const message = ref('');
const messageType = ref<'success' | 'error'>('success');

// 方法
const goBackToDatabase = () => {
  router.push({
    name: 'DatabaseView',
    params: { id: datasetId.value }
  });
};

const goToManualCreation = () => {
  // 跳转到手动创建页面，并传递版本信息
  router.push({
    name: 'ManualStdQaCreation',
    params: { datasetId: datasetId.value },
    query: { 
      fromVersion: 'true',
      versionId: versionId.value 
    }
  });
};

const showMessage = (msg: string, type: 'success' | 'error' = 'success') => {
  message.value = msg;
  messageType.value = type;
  setTimeout(() => {
    message.value = '';
  }, 3000);
};

const loadDataset = async () => {
  try {
    currentDataset.value = await datasetService.getDataset(Number(datasetId.value));
  } catch (error) {
    showMessage('加载数据集信息失败', 'error');
    console.error('Load dataset error:', error);
  }
};

const loadVersion = async () => {
  try {
    currentVersion.value = await versionService.getVersion(Number(versionId.value));
  } catch (error) {
    showMessage('加载版本信息失败', 'error');
    console.error('Load version error:', error);
  }
};

const loadStdQuestions = async () => {
  try {
    // 加载版本中的标准问答对
    stdQuestions.value = await versionService.getVersionQuestions(Number(versionId.value));
    
    // 初始化修改项列表 - 检查哪些问题已经被修改
    modifiedItems.value = stdQuestions.value
      .filter(question => question.is_modified)
      .map(question => question.id);
      
  } catch (error) {
    showMessage('加载问答对失败', 'error');
    console.error('Load std questions error:', error);
  }
};

const editQuestion = (question: any) => {
  selectedQuestion.value = question;
  editForm.value = {
    id: question.id,
    body: question.body,
    question_type: question.question_type,
    tags: question.tags ? [...question.tags] : [],
    std_answers: question.std_answers ? question.std_answers.map((answer: any) => ({
      id: answer.id,
      answer: answer.answer,
      answered_by: answer.answered_by,
      scoring_points: answer.scoring_points ? answer.scoring_points.map((point: any) => ({
        id: point.id,
        answer: point.answer,
        point_order: point.point_order
      })) : []
    })) : []
  };
  showEditModal.value = true;
};

const saveEdit = async () => {
  editSaving.value = true;
  try {
    // 这里实现保存编辑的逻辑，需要后端支持版本管理
    const updatedQuestion = await versionService.updateVersionQuestion(
      Number(currentVersion.value.id), 
      editForm.value.id, 
      editForm.value
    );
    
    // 更新本地数据
    const index = stdQuestions.value.findIndex(q => q.id === editForm.value.id);
    if (index !== -1) {
      stdQuestions.value[index] = updatedQuestion;
    }
    
    // 添加到修改列表
    if (!modifiedItems.value.includes(editForm.value.id)) {
      modifiedItems.value.push(editForm.value.id);
    }
    
    showMessage('保存成功', 'success');
    closeEditModal();
  } catch (error) {
    showMessage('保存失败', 'error');
    console.error('Save edit error:', error);
  } finally {
    editSaving.value = false;
  }
};

const deleteQuestion = async (questionId: number) => {
  if (!confirm('确定要删除这个问答对吗？')) return;
  
  try {
    await versionService.deleteVersionQuestion(Number(currentVersion.value.id), questionId);
    stdQuestions.value = stdQuestions.value.filter(q => q.id !== questionId);
    modifiedItems.value = modifiedItems.value.filter(id => id !== questionId);
    showMessage('删除成功', 'success');
  } catch (error) {
    showMessage('删除失败', 'error');
    console.error('Delete question error:', error);
  }
};

const createNewQA = async () => {
  createSaving.value = true;
  try {
    const newQuestion = await versionService.createVersionQA(Number(currentVersion.value.id), {
      question: {
        body: createForm.value.body,
        question_type: createForm.value.question_type,
        tags: []
      },
      answer: {
        answer: createForm.value.answer
      }    });
    
    stdQuestions.value.push(newQuestion);
    
    // 新创建的问答对也算作修改项
    if (newQuestion.id && !modifiedItems.value.includes(newQuestion.id)) {
      modifiedItems.value.push(newQuestion.id);
    }
    
    showMessage('创建成功', 'success');
    closeCreateModal();
  } catch (error) {
    showMessage('创建失败', 'error');
    console.error('Create QA error:', error);
  } finally {
    createSaving.value = false;
  }
};

const saveVersion = async () => {
  if (!hasChanges.value) {
    showMessage('没有修改需要保存', 'error');
    return;
  }
  
  if (!versionWorkId.value) {
    showMessage('版本工作ID不存在，无法创建版本', 'error');
    return;
  }
  
  // 询问用户确认
  const confirmed = confirm('确定要创建新版本吗？\n\n这将应用所有修改并创建数据集的新版本。');
  if (!confirmed) return;
  
  saving.value = true;
  try {
    const result = await datasetVersionWorkService.createNewVersion(versionWorkId.value);
    
    if (result.success) {
      showMessage(`版本创建成功！新版本号: ${result.version_info.version}`, 'success');
      
      // 跳转回数据库管理
      setTimeout(() => {
        goBackToDatabase();
      }, 2000);
    } else {
      showMessage(result.message || '版本创建失败', 'error');
    }
  } catch (error: any) {
    showMessage(error.response?.data?.detail || '版本创建失败', 'error');
    console.error('Create version error:', error);
  } finally {
    saving.value = false;
  }
};

const previewChanges = () => {
  // TODO: 实现预览更改功能
  showMessage('预览功能开发中...', 'error');
};

// 标签编辑
const addTag = () => {
  const tag = newTag.value.trim();
  if (tag && !editForm.value.tags.includes(tag)) {
    editForm.value.tags.push(tag);
    newTag.value = '';
  }
};

const removeTag = (index: number) => {
  editForm.value.tags.splice(index, 1);
};

// 答案编辑
const addAnswer = () => {
  editForm.value.std_answers.push({
    answer: '',
    answered_by: '',
    scoring_points: []
  });
};

const removeAnswer = (index: number) => {
  editForm.value.std_answers.splice(index, 1);
};

const addScoringPoint = (answerIndex: number) => {
  const answer = editForm.value.std_answers[answerIndex];
  answer.scoring_points.push({
    answer: '',
    point_order: answer.scoring_points.length + 1
  });
};

const removeScoringPoint = (answerIndex: number, pointIndex: number) => {
  editForm.value.std_answers[answerIndex].scoring_points.splice(pointIndex, 1);
};

// 弹窗控制
const closeEditModal = () => {
  showEditModal.value = false;
  editForm.value = {};
  selectedQuestion.value = null;
  newTag.value = '';
};

const closeCreateModal = () => {
  showCreateModal.value = false;
  createForm.value = {
    body: '',
    question_type: 'text',
    answer: ''
  };
};

const closeImportModal = () => {
  showImportModal.value = false;
  clearImportPreview();
};

// 文件导入
const handleDrop = (e: DragEvent) => {
  e.preventDefault();
  isDragOver.value = false;
  const files = e.dataTransfer?.files;
  if (files && files.length > 0) {
    handleFile(files[0]);
  }
};

const handleFileSelect = (e: Event) => {
  const target = e.target as HTMLInputElement;
  const files = target.files;
  if (files && files.length > 0) {
    handleFile(files[0]);
  }
};

const handleFile = async (file: File) => {
  importError.value = '';
  try {
    const text = await file.text();
    const data = JSON.parse(text);
    
    if (Array.isArray(data)) {
      importPreviewData.value = data;
    } else {
      importError.value = 'JSON文件应该包含一个数组';
    }
  } catch (error) {
    importError.value = '文件格式错误，请检查JSON格式是否正确';
  }
};

const clearImportPreview = () => {
  importPreviewData.value = [];
  importError.value = '';
  if (fileInput.value) {
    fileInput.value.value = '';
  }
};

const confirmImport = async () => {
  importing.value = true;
  try {
    const response = await versionService.importDataToVersion(Number(currentVersion.value.id), importPreviewData.value);
    
    // 重新加载数据
    await loadStdQuestions();
    showMessage(`成功导入 ${response.imported} 条记录`, 'success');
    closeImportModal();
  } catch (error) {
    showMessage('导入失败', 'error');
    console.error('Import error:', error);
  } finally {
    importing.value = false;
  }
};

// 初始化版本工作
const initVersionWork = async () => {
  try {
    // 检查路由参数中是否传递了versionWorkId
    const workId = route.query.workId as string;
    if (workId) {
      versionWorkId.value = Number(workId);
      return;
    }
    
    // 如果没有传递工作ID，创建一个新的版本工作
    if (currentDataset.value && currentVersion.value) {
      const newVersionWork = await datasetVersionWorkService.createVersionWork({
        dataset_id: Number(datasetId.value),
        current_version: currentVersion.value.version || 1,
        target_version: (currentVersion.value.version || 1) + 1,
        work_description: `编辑版本 ${currentVersion.value.version || 1} 创建新版本`,
        notes: `基于版本 ${currentVersion.value.version || 1} 的修改`
      });
      
      versionWorkId.value = newVersionWork.id;
      
      // 加载当前版本的数据到版本工作中
      await datasetVersionWorkService.loadDatasetToVersionWork(
        newVersionWork.id,
        Number(datasetId.value),
        currentVersion.value.version || 1
      );
      
      // 重新加载数据以显示加载的内容
      await loadVersionWorkData();
      
      showMessage('版本工作环境初始化成功', 'success');
    }
  } catch (error: any) {
    showMessage('初始化版本工作失败: ' + (error.response?.data?.detail || error.message), 'error');
    console.error('Init version work error:', error);
  }
};

const loadVersionWorkData = async () => {
  if (!versionWorkId.value) return;
  
  try {
    // 获取版本工作的详细信息
    const versionWork = await datasetVersionWorkService.getVersionWork(versionWorkId.value);
    
    // 从版本工作中构建标准问题列表
    const workQuestions = versionWork.version_questions || [];
    stdQuestions.value = workQuestions.map((vq: any) => {
      // 如果是新问题或修改的问题，使用修改后的内容
      const questionData = vq.is_new || vq.is_modified ? {
        id: vq.id,
        body: vq.modified_body || '',
        question_type: vq.modified_question_type || 'text',
        is_valid: true,
        tags: vq.version_tags?.map((tag: any) => tag.tag_label) || [],
        std_answers: vq.version_answers?.map((va: any) => ({
          id: va.id,
          answer: va.modified_answer || '',
          answered_by: va.modified_answered_by,
          scoring_points: va.version_scoring_points?.map((vp: any) => ({
            id: vp.id,
            answer: vp.modified_answer || '',
            point_order: vp.modified_point_order || 0
          })) || []
        })) || []
      } : {
        // 未修改的问题，使用原始内容
        id: vq.original_question?.id || vq.id,
        body: vq.original_question?.body || '',
        question_type: vq.original_question?.question_type || 'text',
        is_valid: vq.original_question?.is_valid || true,
        tags: vq.version_tags?.map((tag: any) => tag.tag_label) || [],
        std_answers: vq.original_question?.std_answers?.map((answer: any) => ({
          id: answer.id,
          answer: answer.answer,
          answered_by: answer.answered_by,
          scoring_points: answer.scoring_points || []
        })) || []
      };
      
      return questionData;
    }).filter((q: any) => !workQuestions.find((vq: any) => vq.id === q.id && vq.is_deleted));
    
    // 计算修改的项目
    modifiedItems.value = workQuestions
      .filter((vq: any) => vq.is_modified || vq.is_new || vq.is_deleted)
      .map((vq: any) => vq.id);
      
  } catch (error: any) {
    showMessage('加载版本工作数据失败: ' + (error.response?.data?.detail || error.message), 'error');
    console.error('Load version work data error:', error);
  }
};

// 生命周期
onMounted(async () => {
  await loadDataset();
  await loadVersion();
  await loadStdQuestions();
  await initVersionWork();
});
</script>

<style scoped>
.version-edit-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.back-btn {
  padding: 8px 16px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  text-decoration: none;
}

.back-btn:hover {
  background: #5a6268;
}

.title-section h2 {
  margin: 0;
  color: #333;
}

.subtitle {
  margin: 5px 0 0 0;
  color: #666;
  font-size: 14px;
}

.version-description {
  margin: 8px 0 0 0;
  color: #555;
  font-size: 13px;
  font-style: italic;
  background: #f8f9fa;
  padding: 4px 8px;
  border-radius: 4px;
  border-left: 3px solid #007bff;
}

.save-version-btn {
  padding: 10px 20px;
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(40, 167, 69, 0.2);
}

.save-version-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #218838 0%, #1abc9c 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(40, 167, 69, 0.3);
}

.save-version-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.version-description-section {
  margin-bottom: 30px;
}

.description-card {
  background: white;
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  max-width: 600px;
  margin: 0 auto;
}

.description-card h3 {
  margin: 0 0 20px 0;
  color: #333;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.form-control {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-control:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.start-edit-btn {
  padding: 12px 24px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 500;
}

.start-edit-btn:hover:not(:disabled) {
  background: #0056b3;
}

.start-edit-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 15px 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.stats {
  display: flex;
  gap: 20px;
}

.stat-item {
  display: flex;
  gap: 5px;
  font-size: 14px;
}

.stat-label {
  color: #666;
}

.stat-value {
  font-weight: bold;
  color: #333;
}

.stat-value.modified {
  color: #28a745;
}

.toolbar-right {
  display: flex;
  gap: 10px;
}

.import-btn,
.create-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}

.import-btn {
  background: #17a2b8;
  color: white;
}

.import-btn:hover {
  background: #138496;
}

.create-btn {
  background: #28a745;
  color: white;
}

.create-btn:hover {
  background: #218838;
}

.qa-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.qa-item {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: all 0.3s ease;
}

.qa-item.modified {
  border-left: 4px solid #28a745;
}

.qa-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
}

.qa-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.qa-id {
  font-weight: bold;
  color: #007bff;
}

.modified-badge {
  background: #28a745;
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.qa-actions {
  display: flex;
  gap: 8px;
}

.edit-btn,
.delete-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.edit-btn {
  background: #007bff;
  color: white;
}

.edit-btn:hover {
  background: #0056b3;
}

.delete-btn {
  background: #dc3545;
  color: white;
}

.delete-btn:hover {
  background: #c82333;
}

.qa-content {
  padding: 20px;
}

.question-section,
.answers-section {
  margin-bottom: 20px;
}

.question-section h4,
.answers-section h4 {
  margin: 0 0 10px 0;
  color: #333;
  font-size: 16px;
}

.question-text {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 10px;
  line-height: 1.5;
}

.question-meta {
  display: flex;
  align-items: center;
  gap: 15px;
  font-size: 13px;
}

.question-type {
  color: #6c757d;
}

.tags {
  display: flex;
  gap: 6px;
}

.tag {
  background: #007bff;
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
}

.answer-item {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 10px;
}

.answer-text {
  margin-bottom: 8px;
  line-height: 1.5;
}

.answer-meta {
  font-size: 13px;
  color: #6c757d;
  display: flex;
  gap: 15px;
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.edit-modal,
.create-modal,
.import-modal {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 800px;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #dee2e6;
}

.modal-header h3 {
  margin: 0;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
  padding: 0;
  width: 30px;
  height: 30px;
}

.close-btn:hover {
  color: #333;
}

.modal-content {
  padding: 20px;
}

.tags-editor {
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 10px;
}

.current-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
  min-height: 24px;
}

.tag-item {
  display: inline-flex;
  align-items: center;
  background: #007bff;
  color: white;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  gap: 4px;
}

.remove-tag-btn {
  background: rgba(255, 255, 255, 0.3);
  border: none;
  color: white;
  border-radius: 50%;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 12px;
}

.add-tag {
  display: flex;
  gap: 8px;
  align-items: center;
}

.add-tag input {
  flex: 1;
}

.add-tag-btn {
  padding: 6px 12px;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.answers-editor {
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 15px;
}

.answer-edit-item {
  border: 1px solid #e9ecef;
  border-radius: 4px;
  padding: 15px;
  margin-bottom: 15px;
}

.answer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.remove-answer-btn {
  background: #dc3545;
  color: white;
  border: none;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.answer-meta-edit {
  margin: 10px 0;
}

.form-control.small {
  max-width: 200px;
  padding: 6px 8px;
  font-size: 13px;
}

.scoring-points-section {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #e9ecef;
}

.scoring-points-list {
  margin-bottom: 10px;
}

.scoring-point-item {
  display: flex;
  gap: 10px;
  align-items: end;
  margin-bottom: 10px;
}

.point-controls {
  display: flex;
  gap: 5px;
  align-items: center;
}

.remove-point-btn {
  background: #dc3545;
  color: white;
  border: none;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  white-space: nowrap;
}

.add-point-btn,
.add-answer-btn {
  background: #17a2b8;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.add-point-btn:hover,
.add-answer-btn:hover {
  background: #138496;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #dee2e6;
}

.cancel-btn {
  padding: 8px 16px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.cancel-btn:hover {
  background: #5a6268;
}

.save-btn {
  padding: 8px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.save-btn:hover:not(:disabled) {
  background: #0056b3;
}

.save-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

/* 文件上传样式 */
.upload-area {
  border: 2px dashed #dee2e6;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  margin-bottom: 20px;
  transition: all 0.3s ease;
}

.upload-area.drag-over {
  border-color: #007bff;
  background: #f0f8ff;
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

.upload-icon {
  font-size: 48px;
}

.select-file-btn {
  padding: 10px 20px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.select-file-btn:hover {
  background: #0056b3;
}

.import-preview {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 15px;
}

/* 导入预览表格样式 */
.preview-table-container {
  margin: 15px 0;
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #dee2e6;
  border-radius: 4px;
}

.preview-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.preview-table th {
  background: #f8f9fa;
  padding: 10px 8px;
  text-align: left;
  font-weight: 500;
  border-bottom: 1px solid #dee2e6;
  position: sticky;
  top: 0;
  z-index: 1;
}

.preview-table td {
  padding: 8px;
  border-bottom: 1px solid #f1f3f4;
}

.preview-cell {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  word-break: break-word;
}

.preview-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.preview-tag {
  background: #e9ecef;
  color: #495057;
  padding: 1px 6px;
  border-radius: 8px;
  font-size: 11px;
}

.preview-note {
  font-size: 12px;
  color: #6c757d;
  text-align: center;
  margin: 10px 0 0 0;
  padding: 8px;
  background: #f8f9fa;
  border-top: 1px solid #dee2e6;
}

.preview-btn {
  background: #6c757d;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  cursor: pointer;
  margin-right: 10px;
  transition: background-color 0.2s ease;
}

.preview-btn:hover:not(:disabled) {
  background: #5a6268;
}

.preview-btn:disabled {
  background: #e9ecef;
  color: #6c757d;
  cursor: not-allowed;
}
</style>
