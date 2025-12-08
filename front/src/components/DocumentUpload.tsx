/**
 * Document Upload Component (Wrapper)
 *
 * This component provides the DocumentUploadFallback component as the default
 * implementation to avoid react-dropzone dependency issues while maintaining
 * the same interface and functionality.
 *
 * @author Knowledge Base Document Management System
 * @version 1.0.0
 */

import React from 'react';
import DocumentUploadFallback from './DocumentUploadFallback';

// Re-export the fallback component with the same interface
const DocumentUpload = React.forwardRef<any, any>((props, ref) => {
  return <DocumentUploadFallback {...props} ref={ref} />;
});

DocumentUpload.displayName = 'DocumentUpload';

export default DocumentUpload;