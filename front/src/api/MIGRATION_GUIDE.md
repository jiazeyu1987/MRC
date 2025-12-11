# Frontend API Client Migration Guide

This guide helps migrate from the old API structure to the new modular API client architecture.

## Overview of Changes

The frontend API clients have been refactored from monolithic files to a modular, resource-specific architecture with improved error handling, caching, and TypeScript support.

### Key Improvements

1. **Modular Architecture**: Split by resource domain (knowledge base, documents, conversations, etc.)
2. **Enhanced Error Handling**: Centralized error handling with detailed error information
3. **Intelligent Caching**: Built-in caching with multiple strategies (cache-first, network-first, SWR)
4. **Type Safety**: Comprehensive TypeScript interfaces and types
5. **Unified Management**: Single API manager for configuration and monitoring
6. **Better Developer Experience**: Auto-completion, type hints, and consistent APIs

## Migration Path

### 1. Old API Usage (Before)

```typescript
// Old way - importing from large monolithic files
import { knowledgeApi } from '../api/knowledgeApi';
import { roleApi } from '../api/roleApi';

// Using the API
const knowledgeBases = await knowledgeApi.getKnowledgeBases();
const roles = await roleApi.getRoles();
```

### 2. New API Usage (After)

```typescript
// New way - importing from modular API clients
import { api, apiManager } from '../api';
import { CacheStrategy } from '../api/shared/cache-manager';

// Using the API (same interface, better implementation)
const knowledgeBases = await api.knowledgeBase.listKnowledgeBases();
const roles = await api.role.listRoles(); // Note: method names may be slightly different

// Or using the manager directly
const kbClient = apiManager.getClient('knowledgeBase');
const knowledgeBases = await kbClient.listKnowledgeBases();

// With caching
const knowledgeBases = await api.knowledgeBase.listKnowledgeBases({
  cache: { strategy: CacheStrategy.CACHE_FIRST, ttl: 60000 }
});
```

## Specific API Changes

### Knowledge Base API

**Before:**
```typescript
import { knowledgeApi } from '../api/knowledgeApi';

const kbs = await knowledgeApi.getKnowledgeBases();
const kb = await knowledgeApi.getKnowledgeBase(id);
const newKb = await knowledgeApi.createKnowledgeBase(data);
```

**After:**
```typescript
import { api } from '../api';

const kbs = await api.knowledgeBase.listKnowledgeBases();
const kb = await api.knowledgeBase.getKnowledgeBase(id);
const newKb = await api.knowledgeBase.createKnowledgeBase(data);
```

### Document API

**Before:**
```typescript
import { knowledgeApi } from '../api/knowledgeApi';

const docs = await knowledgeApi.getDocuments(knowledgeBaseId);
const doc = await knowledgeApi.getDocument(knowledgeBaseId, documentId);
```

**After:**
```typescript
import { api } from '../api';

const docs = await api.documents.listDocuments(knowledgeBaseId);
const doc = await api.documents.getDocument(knowledgeBaseId, documentId);
```

### Conversation API

**Before:**
```typescript
import { conversationApi } from '../api/conversationApi';

const conversations = await conversationApi.getConversations(knowledgeBaseId);
const messages = await conversationApi.getMessages(knowledgeBaseId, conversationId);
```

**After:**
```typescript
import { api } from '../api';

const conversations = await api.conversations.listConversations(knowledgeBaseId);
const messages = await api.conversations.getMessages(knowledgeBaseId, conversationId);
```

### RAGFlow Integration API (NEW)

**New functionality:**
```typescript
import { api } from '../api';

// RAGFlow chat
const response = await api.ragflow.chatInteraction({
  message: "Hello, how can you help me?",
  conversationId: "conv-123"
});

// Document retrieval
const results = await api.ragflow.retrieveDocuments({
  datasetId: "dataset-123",
  query: "machine learning",
  topK: 5
});

// Test connection
const connection = await api.ragflow.testConnection();
```

### Analytics API (NEW)

**New functionality:**
```typescript
import { api } from '../api';

// Search analytics
const analytics = await api.analytics.getSearchAnalytics(knowledgeBaseId, {
  days: 30,
  groupBy: 'day'
});

// System overview
const overview = await api.analytics.getSystemOverview();

// Performance metrics
const metrics = await api.analytics.getPerformanceMetrics({
  startDate: '2024-01-01',
  endDate: '2024-01-31'
});
```

## Error Handling Improvements

### New Error Handling Pattern

```typescript
import { api, ApiError } from '../api';

try {
  const result = await api.knowledgeBase.getKnowledgeBase(id);
  return result;
} catch (error) {
  if (error instanceof ApiError) {
    console.error('API Error:', error.message);
    console.error('Status:', error.status);
    console.error('Code:', error.code);
    console.error('Details:', error.details);
  }
  throw error;
}
```

### Automatic Error Handling

The new API clients automatically handle and format error messages, providing more consistent and helpful error information.

## Caching Features

### Basic Caching

```typescript
import { api, CacheStrategy } from '../api';

// Cache-first strategy (default)
const data = await api.knowledgeBase.listKnowledgeBases({
  cache: { strategy: CacheStrategy.CACHE_FIRST, ttl: 300000 } // 5 minutes
});

// Network-first strategy
const data = await api.knowledgeBase.listKnowledgeBases({
  cache: { strategy: CacheStrategy.NETWORK_FIRST, ttl: 300000 }
});

// Stale-while-revalidate strategy
const data = await api.knowledgeBase.listKnowledgeBases({
  cache: { strategy: CacheStrategy.STALE_WHILE_REVALIDATE, ttl: 300000 }
});
```

### Cache Management

```typescript
import { apiManager } from '../api';

// Clear all cache
apiManager.clearCache();

// Clear cache by pattern
apiManager.clearCacheByPattern('/knowledge-bases/*');

// Get cache statistics
const stats = apiManager.getCacheStats();
console.log('Cache hit rate:', stats.hitRate);
```

## Configuration

### Global Configuration

```typescript
import { initializeApi, CacheStrategy } from '../api';

const apiManager = initializeApi({
  baseUrl: '/api',
  timeout: 30000,
  retryAttempts: 3,
  enableCache: true,
  cacheOptions: {
    ttl: 5 * 60 * 1000, // 5 minutes
    maxSize: 100,
    strategy: CacheStrategy.CACHE_FIRST
  }
});
```

### Per-Request Configuration

```typescript
import { api } from '../api';

const data = await api.knowledgeBase.listKnowledgeBases({
  cache: {
    strategy: CacheStrategy.NETWORK_FIRST,
    ttl: 60000,
    tags: ['knowledge-bases']
  },
  timeout: 10000
});
```

## Backward Compatibility

The old API imports are still available for gradual migration:

```typescript
// Still works (but will be deprecated in future)
import { knowledgeApi } from '../api/knowledgeApi';
import { roleApi } from '../api/roleApi';
import { flowApi } from '../api/flowApi';
import { sessionApi } from '../api/sessionApi';
```

## Health Monitoring

### Connection Testing

```typescript
import { apiManager } from '../api';

// Test all API connections
const connections = await apiManager.testConnections();
console.log('API Connections:', connections);

// Health check
const health = await apiManager.healthCheck();
console.log('System Health:', health.status);
```

### Usage Statistics

```typescript
import { apiManager } from '../api';

const stats = apiManager.getUsageStats();
console.log('API Usage:', stats);
```

## Migration Checklist

### For Each Component

1. **Update Imports**:
   ```typescript
   // From
   import { knowledgeApi } from '../api/knowledgeApi';

   // To
   import { api } from '../api';
   ```

2. **Update Method Calls**:
   ```typescript
   // From
   const kbs = await knowledgeApi.getKnowledgeBases();

   // To
   const kbs = await api.knowledgeBase.listKnowledgeBases();
   ```

3. **Add Error Handling** (optional but recommended):
   ```typescript
   try {
     const data = await api.knowledgeBase.listKnowledgeBases();
     return data;
   } catch (error) {
     // Handle error appropriately
     throw error;
   }
   ```

4. **Add Caching** (optional):
   ```typescript
   const data = await api.knowledgeBase.listKnowledgeBases({
     cache: { strategy: CacheStrategy.CACHE_FIRST, ttl: 300000 }
   });
   ```

### Testing Your Migration

1. **Compile Check**: Ensure TypeScript compilation succeeds
2. **Runtime Test**: Test all API calls in your component
3. **Error Handling**: Verify error handling works correctly
4. **Performance**: Check if caching improves performance

## Benefits of Migration

1. **Better Performance**: Intelligent caching reduces unnecessary API calls
2. **Improved Reliability**: Better error handling and retry logic
3. **Type Safety**: Comprehensive TypeScript support
4. **Developer Experience**: Better auto-completion and debugging
5. **Monitoring**: Built-in health checks and usage statistics
6. **Future-Proof**: Modular architecture easier to maintain and extend

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're importing from `'../api'` not specific API files
2. **Method Names**: Some method names may have changed (e.g., `getKnowledgeBases` → `listKnowledgeBases`)
3. **Type Errors**: Update your type definitions to use the new interfaces
4. **Cache Issues**: Cache is opt-in, won't break existing functionality

### Getting Help

If you encounter issues during migration:

1. Check this guide for common patterns
2. Look at the new API client implementations in `/src/api/`
3. Use the browser dev tools to inspect API requests
4. Check the console for error messages

## Timeline

- **Phase 1**: New API clients available alongside old ones (current)
- **Phase 2**: Deprecation warnings for old APIs (future)
- **Phase 3**: Removal of old APIs (future, with ample notice)

The migration is designed to be gradual - you can migrate components one at a time without breaking the application.