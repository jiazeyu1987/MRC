const express = require('express');
const cors = require('cors');
const path = require('path');

const app = express();
const PORT = 5010;

// Middleware
app.use(cors());
app.use(express.json());

// Mock knowledge base data (can be replaced with real data later)
const mockKnowledgeBases = [
  {
    id: 1,
    name: "物理知识库",
    description: "包含物理学相关概念、公式、定律和应用案例，涵盖力学、电磁学、热力学、光学、量子物理等领域",
    status: "active",
    document_count: 156,
    created_at: "2025-12-01T00:00:00Z",
    ragflow_dataset_id: "physics_dataset_001"
  },
  {
    id: 2,
    name: "数学知识库",
    description: "数学概念、公式、定理和解题方法，包括代数、几何、微积分、概率论、统计学等数学分支",
    status: "active",
    document_count: 234,
    created_at: "2025-12-02T00:00:00Z",
    ragflow_dataset_id: "math_dataset_002"
  },
  {
    id: 3,
    name: "化学知识库",
    description: "化学反应原理、元素周期表、化学键、分子结构、有机化学、无机化学和生物化学内容",
    status: "active",
    document_count: 189,
    created_at: "2025-12-03T00:00:00Z",
    ragflow_dataset_id: "chemistry_dataset_003"
  },
  {
    id: 4,
    name: "生物知识库",
    description: "生物结构、生命过程、生态系统、遗传学、进化论、细胞生物学和分子生物学相关知识",
    status: "active",
    document_count: 178,
    created_at: "2025-12-04T00:00:00Z",
    ragflow_dataset_id: "biology_dataset_004"
  },
  {
    id: 5,
    name: "历史知识库",
    description: "历史事件、历史人物、文明发展、朝代更替、战争与和平、文化传承和社会变迁",
    status: "active",
    document_count: 312,
    created_at: "2025-12-05T00:00:00Z",
    ragflow_dataset_id: "history_dataset_005"
  },
  {
    id: 6,
    name: "计算机科学知识库",
    description: "编程语言、算法与数据结构、计算机网络、数据库、操作系统、人工智能和软件工程",
    status: "active",
    document_count: 267,
    created_at: "2025-12-06T00:00:00Z",
    ragflow_dataset_id: "cs_dataset_006"
  },
  {
    id: 7,
    name: "文学知识库",
    description: "中外文学作品、作家介绍、文学流派、文学理论、诗歌、散文、小说和戏剧文学",
    status: "inactive",
    document_count: 145,
    created_at: "2025-12-07T00:00:00Z",
    ragflow_dataset_id: "literature_dataset_007"
  },
  {
    id: 8,
    name: "地理知识库",
    description: "自然地理、人文地理、世界地理、中国地理、地图学、气候学、地形地貌和地理信息系统",
    status: "active",
    document_count: 203,
    created_at: "2025-12-08T00:00:00Z",
    ragflow_dataset_id: "geography_dataset_008"
  }
];

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({
    success: true,
    message: 'Backend proxy server is running',
    timestamp: new Date().toISOString()
  });
});

// Knowledge bases endpoint
app.get('/api/knowledge-bases', (req, res) => {
  const { page = 1, page_size = 20, search = '', status = '' } = req.query;

  let filteredKbs = [...mockKnowledgeBases];

  // Apply search filter
  if (search) {
    filteredKbs = filteredKbs.filter(kb =>
      kb.name.toLowerCase().includes(search.toLowerCase()) ||
      kb.description.toLowerCase().includes(search.toLowerCase())
    );
  }

  // Apply status filter
  if (status) {
    filteredKbs = filteredKbs.filter(kb => kb.status === status);
  }

  // Apply pagination
  const startIndex = (page - 1) * page_size;
  const endIndex = startIndex + parseInt(page_size);
  const paginatedItems = filteredKbs.slice(startIndex, endIndex);

  res.json({
    success: true,
    data: {
      items: paginatedItems,
      pagination: {
        page: parseInt(page),
        page_size: parseInt(page_size),
        total: filteredKbs.length,
        total_pages: Math.ceil(filteredKbs.length / page_size)
      }
    }
  });
});

// Refresh knowledge bases endpoint (mock implementation)
app.post('/api/knowledge-bases', (req, res) => {
  const { action } = req.body;

  if (action === 'refresh_all') {
    // Simulate refresh process
    setTimeout(() => {
      console.log('Knowledge bases refreshed');
    }, 1000);

    res.json({
      success: true,
      data: {
        message: 'Knowledge bases refresh initiated',
        refreshed_count: mockKnowledgeBases.length
      }
    });
  } else {
    res.status(400).json({
      success: false,
      message: 'Unknown action'
    });
  }
});

// Knowledge base details endpoint
app.get('/api/knowledge-bases/:id', (req, res) => {
  const id = parseInt(req.params.id);
  const kb = mockKnowledgeBases.find(kb => kb.id === id);

  if (!kb) {
    return res.status(404).json({
      success: false,
      message: 'Knowledge base not found'
    });
  }

  res.json({
    success: true,
    data: kb
  });
});

// Catch all other routes
app.use('*', (req, res) => {
  res.status(404).json({
    success: false,
    message: 'Endpoint not found',
    path: req.originalUrl
  });
});

// Error handling
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({
    success: false,
    message: 'Internal server error'
  });
});

app.listen(PORT, () => {
  console.log(`🚀 Backend proxy server running on port ${PORT}`);
  console.log(`📚 Serving ${mockKnowledgeBases.length} knowledge bases`);
  console.log(`🌐 API available at http://localhost:${PORT}/api`);
  console.log(`💡 Health check: http://localhost:${PORT}/api/health`);
});

module.exports = app;