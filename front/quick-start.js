#!/usr/bin/env node

/**
 * 快速启动脚本 - MRC Frontend
 * 用于快速检查和启动前端开发环境
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m'
};

function log(message, color = colors.reset) {
  console.log(`${color}${message}${colors.reset}`);
}

function checkNodeVersion() {
  const version = process.version;
  const majorVersion = parseInt(version.slice(1).split('.')[0]);

  if (majorVersion < 16) {
    log(`❌ Node.js版本过低: ${version} (需要16或更高)`, colors.red);
    return false;
  }

  log(`✅ Node.js版本: ${version}`, colors.green);
  return true;
}

function checkProjectFiles() {
  const requiredFiles = [
    'package.json',
    'vite.config.ts',
    'tsconfig.json',
    'src/main.tsx',
    'src/App.tsx'
  ];

  for (const file of requiredFiles) {
    if (!fs.existsSync(file)) {
      log(`❌ 缺少必需文件: ${file}`, colors.red);
      return false;
    }
  }

  log('✅ 项目文件完整', colors.green);
  return true;
}

function checkDependencies() {
  if (!fs.existsSync('node_modules')) {
    log('❌ 依赖未安装', colors.red);
    log('💡 请运行: npm install', colors.yellow);
    return false;
  }

  if (!fs.existsSync('package-lock.json')) {
    log('⚠️  没有package-lock.json，建议重新安装依赖', colors.yellow);
  }

  log('✅ 依赖已安装', colors.green);
  return true;
}

function checkBackendConnection() {
  // 简单检查vite配置中的后端代理设置
  try {
    const viteConfig = fs.readFileSync('vite.config.ts', 'utf8');
    if (viteConfig.includes('5010')) {
      log('✅ 后端代理配置正确 (端口5010)', colors.green);
      return true;
    } else {
      log('⚠️  后端代理配置可能需要更新', colors.yellow);
      return true;
    }
  } catch (error) {
    log('❌ 无法读取vite配置', colors.red);
    return false;
  }
}

function installDependencies() {
  log('📦 安装依赖...', colors.blue);
  try {
    execSync('npm install', { stdio: 'inherit' });
    log('✅ 依赖安装完成', colors.green);
    return true;
  } catch (error) {
    log('❌ 依赖安装失败', colors.red);
    return false;
  }
}

function startDevServer() {
  log('🚀 启动开发服务器...', colors.blue);
  try {
    execSync('npm run dev', { stdio: 'inherit' });
  } catch (error) {
    if (error.signal === 'SIGINT') {
      log('\n👋 开发服务器已停止', colors.cyan);
    } else {
      log('❌ 启动失败', colors.red);
      process.exit(1);
    }
  }
}

function main() {
  log('🎯 MRC Frontend 启动检查\n', colors.cyan);

  // 执行检查
  const checks = [
    { name: 'Node.js版本', fn: checkNodeVersion },
    { name: '项目文件', fn: checkProjectFiles },
    { name: '依赖包', fn: checkDependencies },
    { name: '后端配置', fn: checkBackendConnection }
  ];

  let allPassed = true;
  for (const { name, fn } of checks) {
    log(`检查 ${name}...`);
    if (!fn()) {
      allPassed = false;
    }
    log('');
  }

  if (!allPassed) {
    log('❌ 启动检查失败\n', colors.red);

    // 如果只是缺少依赖，自动安装
    if (!fs.existsSync('node_modules')) {
      log('尝试自动安装依赖...\n', colors.yellow);
      if (installDependencies()) {
        log('✅ 依赖安装完成，可以重新运行此脚本', colors.green);
      }
    }

    process.exit(1);
  }

  log('✅ 所有检查通过！\n', colors.green);

  // 显示使用说明
  log('📋 使用说明:', colors.blue);
  log('• 前端地址: http://localhost:3000', colors.cyan);
  log('• 后端地址: http://localhost:5010', colors.cyan);
  log('• 按 Ctrl+C 停止服务器\n', colors.cyan);

  // 启动开发服务器
  startDevServer();
}

if (require.main === module) {
  main();
}

module.exports = { checkNodeVersion, checkProjectFiles, checkDependencies };