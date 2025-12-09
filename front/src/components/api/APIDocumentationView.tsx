import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  Code,
  Terminal,
  Send,
  Play,
  Copy,
  Check,
  Download,
  RefreshCw,
  Search,
  Filter,
  Loader2,
  AlertCircle,
  ExternalLink,
  FileText,
  Globe,
  Shield,
  Zap,
  Database,
  MessageSquare,
  Eye,
  EyeOff,
  ChevronDown,
  ChevronRight,
  Key,
  Clock,
  Server
} from 'lucide-react';
import { useTheme } from '../../theme';
import { enhancedApi } from '../../api';
import { APIDocumentation, APIEndpoint, APIExample } from '../../types/enhanced';

interface APIDocumentationViewProps {
  knowledgeBaseId: number;
  knowledgeBaseName: string;
}

const APIDocumentationView: React.FC<APIDocumentationViewProps> = ({
  knowledgeBaseId,
  knowledgeBaseName
}) => {
  const { theme } = useTheme();
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [documentation, setDocumentation] = useState<APIDocumentation | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedEndpoint, setSelectedEndpoint] = useState<APIEndpoint | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [expandedEndpoints, setExpandedEndpoints] = useState<Set<string>>(new Set());
  const [copiedCode, setCopiedCode] = useState<string>('');

  // 加载API文档
  const loadDocumentation = async () => {
    try {
      setError(null);
      const data = await enhancedApi.apiDocumentation.getDocumentation(knowledgeBaseId);
      setDocumentation(data);

      // 设置默认选中的分类
      if (data.endpoints && data.endpoints.length > 0) {
        const categories = [...new Set(data.endpoints.map(ep => ep.category))];
        setSelectedCategory(categories[0]);
      }
    } catch (err) {
      setError('Failed to load API documentation');
      console.error('Documentation loading error:', err);
    }
  };

  // 刷新文档
  const handleRefresh = async () => {
    setRefreshing(true);
    await loadDocumentation();
    setRefreshing(false);
  };

  // 复制代码到剪贴板
  const copyToClipboard = async (text: string, type: string = 'code') => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedCode(type);
      setTimeout(() => setCopiedCode(''), 2000);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  };

  // 导出文档
  const handleExportDocumentation = async () => {
    try {
      await enhancedApi.apiDocumentation.exportDocumentation(knowledgeBaseId, 'markdown');
      // 如果成功，浏览器会开始下载文件
    } catch (err) {
      console.error('Export failed:', err);
      setError('Failed to export documentation');
    }
  };

  // 测试API端点
  const handleTestEndpoint = async (endpoint: APIEndpoint) => {
    if (!endpoint.playground) return;

    try {
      // 这里可以打开一个API测试对话框或跳转到测试页面
      console.log('Testing endpoint:', endpoint);
    } catch (err) {
      console.error('Endpoint test failed:', err);
    }
  };

  // 组件加载时获取数据
  useEffect(() => {
    if (knowledgeBaseId) {
      setLoading(true);
      loadDocumentation().finally(() => setLoading(false));
    }
  }, [knowledgeBaseId]);

  // 过滤端点
  const filteredEndpoints = documentation?.endpoints?.filter(endpoint => {
    const matchesCategory = !selectedCategory || endpoint.category === selectedCategory;
    const matchesSearch = !searchQuery ||
      endpoint.path.toLowerCase().includes(searchQuery.toLowerCase()) ||
      endpoint.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      endpoint.method.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  }) || [];

  // 获取所有分类
  const categories = [...new Set(documentation?.endpoints?.map(ep => ep.category) || [])];

  // 切换端点展开状态
  const toggleEndpointExpanded = (endpointId: string) => {
    const newExpanded = new Set(expandedEndpoints);
    if (newExpanded.has(endpointId)) {
      newExpanded.delete(endpointId);
    } else {
      newExpanded.add(endpointId);
    }
    setExpandedEndpoints(newExpanded);
  };

  // 获取方法颜色
  const getMethodColor = (method: string) => {
    switch (method.toLowerCase()) {
      case 'get':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'post':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'put':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'patch':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'delete':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <div className="text-center">
          <Loader2 className="w-8 h-8 mx-auto animate-spin text-blue-500 mb-4" />
          <p className="text-gray-500">加载API文档中...</p>
        </div>
      </div>
    );
  }

  if (error && !documentation) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 mx-auto text-red-500 mb-4" />
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className={`px-4 py-2 text-sm font-medium text-white rounded-md ${theme.primary} ${theme.primaryHover} disabled:opacity-50 disabled:cursor-not-allowed transition-colors`}
          >
            {refreshing ? '刷新中...' : '重试'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 头部信息 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">API文档</h2>
            <p className="text-sm text-gray-600">知识库: {knowledgeBaseName}</p>
            {documentation?.last_updated && (
              <p className="text-xs text-gray-500 mt-1">
                最后更新: {new Date(documentation.last_updated).toLocaleString('zh-CN')}
              </p>
            )}
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {refreshing ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4 mr-2" />
              )}
              刷新
            </button>
            <button
              onClick={handleExportDocumentation}
              className="flex items-center px-4 py-2 text-sm font-medium text-white rounded-md ${theme.primary} ${theme.primaryHover} transition-colors"
            >
              <Download className="w-4 h-4 mr-2" />
              导出文档
            </button>
          </div>
        </div>

        {/* API信息概览 */}
        {documentation && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center space-x-3">
              <Globe className="w-5 h-5 text-blue-500" />
              <div>
                <p className="text-sm font-medium text-gray-900">基础URL</p>
                <p className="text-xs text-gray-600">{documentation.base_url}</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <Shield className="w-5 h-5 text-green-500" />
              <div>
                <p className="text-sm font-medium text-gray-900">认证方式</p>
                <p className="text-xs text-gray-600">{documentation.authentication}</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <Zap className="w-5 h-5 text-yellow-500" />
              <div>
                <p className="text-sm font-medium text-gray-900">API版本</p>
                <p className="text-xs text-gray-600">{documentation.version}</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <Database className="w-5 h-5 text-purple-500" />
              <div>
                <p className="text-sm font-medium text-gray-900">端点数量</p>
                <p className="text-xs text-gray-600">{documentation.endpoints?.length || 0}</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 搜索和过滤 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex flex-col md:flex-row md:items-center md:space-x-4 space-y-3 md:space-y-0">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="搜索API端点..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div className="flex items-center space-x-2">
            <Filter className="w-5 h-5 text-gray-400" />
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">所有分类</option>
              {categories.map(category => (
                <option key={category} value={category}>{category}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* API端点列表 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">API端点</h3>

          {filteredEndpoints.length > 0 ? (
            <div className="space-y-4">
              {filteredEndpoints.map((endpoint) => (
                <div key={endpoint.id} className="border border-gray-200 rounded-lg overflow-hidden">
                  {/* 端点头部 */}
                  <div
                    className="p-4 bg-gray-50 hover:bg-gray-100 cursor-pointer transition-colors"
                    onClick={() => toggleEndpointExpanded(endpoint.id)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className={`px-2 py-1 text-xs font-medium rounded-md border ${getMethodColor(endpoint.method)}`}>
                          {endpoint.method.toUpperCase()}
                        </div>
                        <code className="text-sm font-mono text-gray-800">{endpoint.path}</code>
                        <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
                          {endpoint.category}
                        </span>
                      </div>
                      <div className="flex items-center space-x-2">
                        {endpoint.playground && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleTestEndpoint(endpoint);
                            }}
                            className="flex items-center px-2 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200 transition-colors"
                          >
                            <Play className="w-3 h-3 mr-1" />
                            测试
                          </button>
                        )}
                        {expandedEndpoints.has(endpoint.id) ? (
                          <ChevronDown className="w-5 h-5 text-gray-400" />
                        ) : (
                          <ChevronRight className="w-5 h-5 text-gray-400" />
                        )}
                      </div>
                    </div>
                    {endpoint.description && (
                      <p className="mt-2 text-sm text-gray-600">{endpoint.description}</p>
                    )}
                  </div>

                  {/* 端点详情 */}
                  {expandedEndpoints.has(endpoint.id) && (
                    <div className="border-t border-gray-200 p-4 space-y-4">
                      {/* 请求参数 */}
                      {endpoint.parameters && endpoint.parameters.length > 0 && (
                        <div>
                          <h4 className="text-sm font-medium text-gray-900 mb-2">请求参数</h4>
                          <div className="overflow-x-auto">
                            <table className="min-w-full text-sm">
                              <thead>
                                <tr className="border-b border-gray-200">
                                  <th className="text-left py-2 px-3 font-medium text-gray-700">参数名</th>
                                  <th className="text-left py-2 px-3 font-medium text-gray-700">类型</th>
                                  <th className="text-left py-2 px-3 font-medium text-gray-700">必需</th>
                                  <th className="text-left py-2 px-3 font-medium text-gray-700">描述</th>
                                </tr>
                              </thead>
                              <tbody>
                                {endpoint.parameters.map((param, index) => (
                                  <tr key={index} className="border-b border-gray-100">
                                    <td className="py-2 px-3 font-mono text-sm">{param.name}</td>
                                    <td className="py-2 px-3">
                                      <span className="px-1 py-0.5 bg-gray-100 rounded text-xs">{param.type}</span>
                                    </td>
                                    <td className="py-2 px-3">
                                      {param.required ? (
                                        <span className="text-red-600">是</span>
                                      ) : (
                                        <span className="text-gray-500">否</span>
                                      )}
                                    </td>
                                    <td className="py-2 px-3 text-gray-600">{param.description}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}

                      {/* 响应示例 */}
                      {endpoint.response_example && (
                        <div>
                          <h4 className="text-sm font-medium text-gray-900 mb-2">响应示例</h4>
                          <div className="relative">
                            <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm">
                              <code>{JSON.stringify(endpoint.response_example, null, 2)}</code>
                            </pre>
                            <button
                              onClick={() => copyToClipboard(JSON.stringify(endpoint.response_example, null, 2), 'response')}
                              className="absolute top-2 right-2 p-2 bg-gray-700 hover:bg-gray-600 rounded text-white transition-colors"
                            >
                              {copiedCode === 'response' ? (
                                <Check className="w-4 h-4" />
                              ) : (
                                <Copy className="w-4 h-4" />
                              )}
                            </button>
                          </div>
                        </div>
                      )}

                      {/* 使用示例 */}
                      {endpoint.examples && endpoint.examples.length > 0 && (
                        <div>
                          <h4 className="text-sm font-medium text-gray-900 mb-2">使用示例</h4>
                          <div className="space-y-3">
                            {endpoint.examples.map((example, index) => (
                              <div key={index} className="border border-gray-200 rounded-lg p-3">
                                <div className="flex items-center justify-between mb-2">
                                  <span className="text-sm font-medium text-gray-700">
                                    {example.language} - {example.description}
                                  </span>
                                  <button
                                    onClick={() => copyToClipboard(example.code, `example-${index}`)}
                                    className="p-1 hover:bg-gray-100 rounded transition-colors"
                                  >
                                    {copiedCode === `example-${index}` ? (
                                      <Check className="w-4 h-4 text-green-600" />
                                    ) : (
                                      <Copy className="w-4 h-4 text-gray-400" />
                                    )}
                                  </button>
                                </div>
                                <pre className="bg-gray-50 text-gray-800 p-3 rounded text-sm overflow-x-auto">
                                  <code>{example.code}</code>
                                </pre>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* 认证信息 */}
                      {endpoint.authentication && (
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                          <div className="flex items-center space-x-2 mb-2">
                            <Key className="w-4 h-4 text-blue-600" />
                            <span className="text-sm font-medium text-blue-900">认证要求</span>
                          </div>
                          <p className="text-sm text-blue-800">{endpoint.authentication}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <FileText className="w-12 h-12 mx-auto text-gray-400 mb-4" />
              <p className="text-gray-500">
                {searchQuery || selectedCategory ? '没有找到匹配的API端点' : '暂无API端点'}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* API使用指南 */}
      {documentation?.usage_guide && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">使用指南</h3>
          <div className="prose prose-sm max-w-none">
            <div
              className="text-gray-700 space-y-4"
              dangerouslySetInnerHTML={{ __html: documentation.usage_guide }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default APIDocumentationView;