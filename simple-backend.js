const http = require('http');
const url = require('url');

// Mock data
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

const mockRoles = [
  {
    id: 1,
    name: "教师",
    description: "具有丰富教学经验的教育者，善于用生动的方式解释复杂概念",
    style: "耐心细致，循循善诱，善于启发思考",
    constraints: "避免直接给出答案，引导学生独立思考",
    focus_points: ["概念解释", "实例演示", "启发提问", "学习指导"]
  },
  {
    id: 2,
    name: "学生",
    description: "积极好学，对未知领域充满好奇心的学习者",
    style: "认真勤奋，勇于提问，乐于接受指导",
    constraints: "避免害羞，积极表达自己的想法",
    focus_points: ["认真听讲", "主动思考", "提出疑问", "练习应用"]
  },
  {
    id: 3,
    name: "专家",
    description: "在特定领域具有深厚专业知识的权威人士",
    style: "严谨专业，逻辑清晰，善于系统分析",
    constraints: "保持客观公正，避免主观偏见",
    focus_points: ["专业分析", "理论阐述", "实证支持", "前沿动态"]
  },
  {
    id: 4,
    name: "评估者",
    description: "负责评价和提供反馈的专业人士",
    style: "客观公正，标准明确，建设性批评",
    constraints: "避免主观情绪，保持评价标准一致",
    focus_points: ["客观评价", "标准把握", "建议反馈", "改进指导"]
  }
];

const mockFlowTemplates = [
  {
    id: 1,
    name: "物理概念教学",
    topic: "牛顿第二定律的应用",
    type: "teaching",
    description: "通过实际案例讲解牛顿第二定律",
    steps: [
      {
        id: 1,
        order: 1,
        speaker_role_ref: "教师",
        target_role_ref: "学生",
        task_type: "ask_question",
        context_scope: "all"
      },
      {
        id: 2,
        order: 2,
        speaker_role_ref: "学生",
        target_role_ref: "教师",
        task_type: "answer_question",
        context_scope: "all"
      },
      {
        id: 3,
        order: 3,
        speaker_role_ref: "教师",
        target_role_ref: "学生",
        task_type: "ask_question",
        context_scope: "all"
      }
    ],
    created_at: "2025-12-01T00:00:00Z",
    updated_at: "2025-12-01T00:00:00Z"
  },
  {
    id: 2,
    name: "数学概念探讨",
    topic: "微积分在现实生活中的应用",
    type: "discussion",
    description: "探讨微积分概念在各个领域的实际应用",
    steps: [
      {
        id: 1,
        order: 1,
        speaker_role_ref: "学生",
        target_role_ref: "专家",
        task_type: "ask_question",
        context_scope: "all"
      },
      {
        id: 2,
        order: 2,
        speaker_role_ref: "专家",
        target_role_ref: "学生",
        task_type: "answer_question",
        context_scope: "all"
      }
    ],
    created_at: "2025-12-02T00:00:00Z",
    updated_at: "2025-12-02T00:00:00Z"
  }
];

const server = http.createServer((req, res) => {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  const parsedUrl = url.parse(req.url, true);
  const path = parsedUrl.pathname;
  const method = req.method;

  console.log(`${method} ${path}`);

  // Health check endpoint
  if (path === '/api/health' && method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      success: true,
      message: 'Simple backend server is running',
      timestamp: new Date().toISOString()
    }));
    return;
  }

  // Knowledge bases endpoint
  if (path === '/api/knowledge-bases' && method === 'GET') {
    const { page = 1, page_size = 20, search = '', status = '' } = parsedUrl.query;

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

    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
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
    }));
    return;
  }

  // Knowledge base details endpoint
  if (path.startsWith('/api/knowledge-bases/') && method === 'GET') {
    const id = parseInt(path.split('/').pop());
    const kb = mockKnowledgeBases.find(kb => kb.id === id);

    if (!kb) {
      res.writeHead(404, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        success: false,
        message: 'Knowledge base not found'
      }));
      return;
    }

    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      success: true,
      data: kb
    }));
    return;
  }

  // Roles endpoint
  if (path === '/api/roles' && method === 'GET') {
    const { page = 1, page_size = 20, search = '' } = parsedUrl.query;

    let filteredRoles = [...mockRoles];

    // Apply search filter
    if (search) {
      filteredRoles = filteredRoles.filter(role =>
        role.name.toLowerCase().includes(search.toLowerCase()) ||
        role.description.toLowerCase().includes(search.toLowerCase()) ||
        role.style.toLowerCase().includes(search.toLowerCase())
      );
    }

    // Apply pagination
    const startIndex = (page - 1) * page_size;
    const endIndex = startIndex + parseInt(page_size);
    const paginatedItems = filteredRoles.slice(startIndex, endIndex);

    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      success: true,
      data: {
        items: paginatedItems,
        pagination: {
          page: parseInt(page),
          page_size: parseInt(page_size),
          total: filteredRoles.length,
          total_pages: Math.ceil(filteredRoles.length / page_size)
        }
      }
    }));
    return;
  }

  // Role details endpoint
  if (path.startsWith('/api/roles/') && method === 'GET') {
    const id = parseInt(path.split('/').pop());
    const role = mockRoles.find(role => role.id === id);

    if (!role) {
      res.writeHead(404, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        success: false,
        message: 'Role not found'
      }));
      return;
    }

    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      success: true,
      data: role
    }));
    return;
  }

  // Flow templates endpoint
  if (path === '/api/flows' && method === 'GET') {
    const { page = 1, page_size = 20, search = '', type = '' } = parsedUrl.query;

    let filteredFlows = [...mockFlowTemplates];

    // Apply search filter
    if (search) {
      filteredFlows = filteredFlows.filter(flow =>
        flow.name.toLowerCase().includes(search.toLowerCase()) ||
        flow.topic.toLowerCase().includes(search.toLowerCase()) ||
        flow.description.toLowerCase().includes(search.toLowerCase())
      );
    }

    // Apply type filter
    if (type) {
      filteredFlows = filteredFlows.filter(flow => flow.type === type);
    }

    // Apply pagination
    const startIndex = (page - 1) * page_size;
    const endIndex = startIndex + parseInt(page_size);
    const paginatedItems = filteredFlows.slice(startIndex, endIndex);

    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      success: true,
      data: {
        items: paginatedItems,
        pagination: {
          page: parseInt(page),
          page_size: parseInt(page_size),
          total: filteredFlows.length,
          total_pages: Math.ceil(filteredFlows.length / page_size)
        }
      }
    }));
    return;
  }

  // Flow template details endpoint
  if (path.startsWith('/api/flows/') && method === 'GET') {
    const id = parseInt(path.split('/').pop());
    const flow = mockFlowTemplates.find(flow => flow.id === id);

    if (!flow) {
      res.writeHead(404, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        success: false,
        message: 'Flow template not found'
      }));
      return;
    }

    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      success: true,
      data: flow
    }));
    return;
  }

  // Create/update flow template endpoint
  if ((path === '/api/flows' && method === 'POST') || (path.startsWith('/api/flows/') && method === 'PUT')) {
    let body = '';
    req.on('data', chunk => {
      body += chunk.toString();
    });
    req.on('end', () => {
      try {
        const flowData = JSON.parse(body);
        const newFlow = {
          ...flowData,
          id: flowData.id || Math.max(...mockFlowTemplates.map(f => f.id)) + 1,
          created_at: flowData.created_at || new Date().toISOString(),
          updated_at: new Date().toISOString()
        };

        res.writeHead(201, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          success: true,
          data: newFlow
        }));
      } catch (error) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          success: false,
          message: 'Invalid JSON'
        }));
      }
    });
    return;
  }

  // Delete flow template endpoint
  if (path.startsWith('/api/flows/') && method === 'DELETE') {
    const id = parseInt(path.split('/').pop());
    const index = mockFlowTemplates.findIndex(flow => flow.id === id);

    if (index === -1) {
      res.writeHead(404, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        success: false,
        message: 'Flow template not found'
      }));
      return;
    }

    const deletedFlow = mockFlowTemplates.splice(index, 1)[0];

    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      success: true,
      data: {
        message: 'Flow template deleted successfully',
        deleted_flow: deletedFlow
      }
    }));
    return;
  }

  // Refresh knowledge bases endpoint
  if (path === '/api/knowledge-bases' && method === 'POST') {
    let body = '';
    req.on('data', chunk => {
      body += chunk.toString();
    });
    req.on('end', () => {
      try {
        const data = JSON.parse(body);
        const { action } = data;

        if (action === 'refresh_all') {
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({
            success: true,
            data: {
              message: 'Knowledge bases refresh initiated',
              refreshed_count: mockKnowledgeBases.length
            }
          }));
        } else {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({
            success: false,
            message: 'Unknown action'
          }));
        }
      } catch (error) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          success: false,
          message: 'Invalid JSON'
        }));
      }
    });
    return;
  }

  // 404 for other routes
  res.writeHead(404, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({
    success: false,
    message: 'Endpoint not found',
    path: path
  }));
});

const PORT = 5010;

server.listen(PORT, () => {
  console.log(`🚀 Simple backend server running on port ${PORT}`);
  console.log(`📚 Serving ${mockKnowledgeBases.length} knowledge bases`);
  console.log(`🌐 API available at http://localhost:${PORT}/api`);
  console.log(`💡 Health check: http://localhost:${PORT}/api/health`);
  console.log(`📖 Knowledge bases: http://localhost:${PORT}/api/knowledge-bases`);
});

server.on('error', (err) => {
  if (err.code === 'EADDRINUSE') {
    console.error(`❌ Port ${PORT} is already in use`);
    console.log('💡 Try stopping other services or use a different port');
  } else {
    console.error('❌ Server error:', err);
  }
});