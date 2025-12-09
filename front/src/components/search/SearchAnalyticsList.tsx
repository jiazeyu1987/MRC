import React, { useState } from 'react';
import { Search, TrendingUp, Users, Clock, MousePointer, Target, Download, Filter, Calendar, RefreshCw, BarChart3 } from 'lucide-react';
import { useTheme } from '../../theme';

interface SearchAnalyticsData {
  totalSearches: number;
  averageResponseTime: number;
  successRate: number;
  topQueries: Array<{ query: string; count: number; trend: 'up' | 'down' | 'stable' }>;
  userActivity: Array<{ date: string; searches: number; uniqueUsers: number }>;
  popularKnowledgeBases: Array<{ name: string; searches: number; percentage: number }>;
}

interface SearchAnalyticsListProps {
  onDetailedAnalytics: () => void;
}

const SearchAnalyticsList: React.FC<SearchAnalyticsListProps> = ({ onDetailedAnalytics }) => {
  const { theme } = useTheme();
  const [timeRange, setTimeRange] = useState<number>(7); // 天数
  const [refreshing, setRefreshing] = useState<boolean>(false);

  // 模拟数据 - 实际应该从API获取
  const analyticsData: SearchAnalyticsData = {
    totalSearches: 1248,
    averageResponseTime: 0.85,
    successRate: 94.5,
    topQueries: [
      { query: 'AI技术应用', count: 156, trend: 'up' },
      { query: '产品使用指南', count: 132, trend: 'stable' },
      { query: '行业发展趋势', count: 98, trend: 'up' },
      { query: '技术支持', count: 87, trend: 'down' },
      { query: '最新功能', count: 76, trend: 'up' }
    ],
    userActivity: [
      { date: '2024-01-15', searches: 156, uniqueUsers: 45 },
      { date: '2024-01-14', searches: 142, uniqueUsers: 38 },
      { date: '2024-01-13', searches: 178, uniqueUsers: 52 },
      { date: '2024-01-12', searches: 165, uniqueUsers: 41 },
      { date: '2024-01-11', searches: 189, uniqueUsers: 58 }
    ],
    popularKnowledgeBases: [
      { name: '技术文档库', searches: 425, percentage: 34.1 },
      { name: '产品手册', searches: 318, percentage: 25.5 },
      { name: '行业报告库', searches: 267, percentage: 21.4 },
      { name: 'FAQ知识库', searches: 156, percentage: 12.5 },
      { name: '研究论文库', searches: 82, percentage: 6.6 }
    ]
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000));
    setRefreshing(false);
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="w-4 h-4 text-green-500" />;
      case 'down':
        return <TrendingUp className="w-4 h-4 text-red-500 transform rotate-180" />;
      case 'stable':
        return <div className="w-4 h-4 bg-gray-400 rounded-full" />;
      default:
        return null;
    }
  };

  const getResponseTimeColor = (time: number) => {
    if (time < 0.5) return 'text-green-600';
    if (time < 1.0) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getSuccessRateColor = (rate: number) => {
    if (rate >= 95) return 'text-green-600';
    if (rate >= 90) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="space-y-6">
      {/* 工具栏 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">搜索分析</h2>
            <div className="flex items-center space-x-3">
              <button
                onClick={handleRefresh}
                disabled={refreshing}
                className={`inline-flex items-center px-4 py-2 text-sm font-medium border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors ${
                  refreshing ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                刷新数据
              </button>
              <button
                onClick={onDetailedAnalytics}
                className={`inline-flex items-center px-4 py-2 text-sm font-medium text-white rounded-lg ${theme.primary} ${theme.primaryHover} transition-colors`}
              >
                <BarChart3 className="w-4 h-4 mr-2" />
                详细分析
              </button>
            </div>
          </div>

          {/* 时间范围选择 */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">时间范围:</label>
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(Number(e.target.value))}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value={1}>最近1天</option>
                <option value={7}>最近7天</option>
                <option value={30}>最近30天</option>
                <option value={90}>最近90天</option>
              </select>
            </div>
            <button className="inline-flex items-center px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
              <Filter className="w-4 h-4 mr-2" />
              筛选
            </button>
            <button className="inline-flex items-center px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
              <Download className="w-4 h-4 mr-2" />
              导出报告
            </button>
          </div>
        </div>
      </div>

      {/* 关键指标卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className={`p-3 rounded-lg ${theme.iconBg} bg-opacity-10`}>
              <Search className={`w-6 h-6 ${theme.text.replace('text-', 'text-')}`} />
            </div>
            <TrendingUp className="w-5 h-5 text-green-500" />
          </div>
          <div className="text-2xl font-bold text-gray-900">{analyticsData.totalSearches.toLocaleString()}</div>
          <div className="text-sm text-gray-600 mt-1">总搜索次数</div>
          <div className="text-xs text-green-600 mt-2">较上周增长 12.5%</div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 rounded-lg bg-blue-100">
              <Clock className="w-6 h-6 text-blue-600" />
            </div>
            <div className={`text-lg font-medium ${getResponseTimeColor(analyticsData.averageResponseTime)}`}>
              {analyticsData.averageResponseTime}s
            </div>
          </div>
          <div className="text-2xl font-bold text-gray-900">{analyticsData.averageResponseTime.toFixed(2)}</div>
          <div className="text-sm text-gray-600 mt-1">平均响应时间</div>
          <div className="text-xs text-blue-600 mt-2">性能良好</div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 rounded-lg bg-green-100">
              <Target className="w-6 h-6 text-green-600" />
            </div>
            <div className={`text-lg font-medium ${getSuccessRateColor(analyticsData.successRate)}`}>
              {analyticsData.successRate}%
            </div>
          </div>
          <div className="text-2xl font-bold text-gray-900">{analyticsData.successRate.toFixed(1)}%</div>
          <div className="text-sm text-gray-600 mt-1">搜索成功率</div>
          <div className="text-xs text-green-600 mt-2">表现优秀</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 热门搜索查询 */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">热门搜索查询</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {analyticsData.topQueries.map((query, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span className="text-sm font-medium text-gray-500 w-6">{index + 1}</span>
                    <span className="text-sm font-medium text-gray-900">{query.query}</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <span className="text-sm text-gray-600">{query.count} 次</span>
                    {getTrendIcon(query.trend)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 热门知识库 */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">热门知识库</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {analyticsData.popularKnowledgeBases.map((kb, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span className="text-sm font-medium text-gray-500 w-6">{index + 1}</span>
                    <span className="text-sm font-medium text-gray-900">{kb.name}</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <span className="text-sm text-gray-600">{kb.searches} 次</span>
                    <span className="text-sm text-gray-500">({kb.percentage}%)</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 用户活动趋势 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">用户活动趋势</h3>
            <div className="flex items-center space-x-4 text-sm text-gray-600">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-blue-500 rounded-full mr-2"></div>
                <span>搜索次数</span>
              </div>
              <div className="flex items-center">
                <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                <span>活跃用户</span>
              </div>
            </div>
          </div>
        </div>
        <div className="p-6">
          <div className="space-y-4">
            {analyticsData.userActivity.map((activity, index) => (
              <div key={index} className="flex items-center justify-between">
                <span className="text-sm text-gray-600">{activity.date}</span>
                <div className="flex items-center space-x-6">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span className="text-sm font-medium text-gray-900">{activity.searches}</span>
                    <span className="text-sm text-gray-600">次搜索</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-sm font-medium text-gray-900">{activity.uniqueUsers}</span>
                    <span className="text-sm text-gray-600">位用户</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SearchAnalyticsList;