// 调试工具：全局错误监控
import { showErrorHistory, clearErrorHistory } from './utils/errorHandler';

// 将调试函数暴露到全局作用域
if (typeof window !== 'undefined') {
  (window as any).debugErrors = {
    show: showErrorHistory,
    clear: clearErrorHistory,
    help: () => {
      console.log(`
🔧 调试工具使用说明:
  debugErrors.show() - 显示错误历史记录
  debugErrors.clear() - 清除错误历史记录
  debugErrors.help() - 显示此帮助信息

📍 错误监控功能:
  - 所有错误将输出到控制台
  - 错误信息包含时间戳和堆栈跟踪
  - 自动保存最近10条错误到sessionStorage
      `);
    }
  };

  // 初始化时显示提示
  console.log('✅ 调试工具已加载，输入 debugErrors.help() 查看使用说明');

  // 监听未捕获的错误
  window.addEventListener('error', (event) => {
    console.error(`[未捕获错误] ${event.message}`, {
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
      error: event.error
    });
  });

  // 监听Promise rejection
  window.addEventListener('unhandledrejection', (event) => {
    console.error('[未处理的Promise拒绝]', event.reason);
  });
}