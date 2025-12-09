import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Database, Settings, ChevronDown, ChevronUp, Search, CheckCircle, AlertCircle, X } from 'lucide-react';
import { useTheme } from '../theme';
import { flowApi, FlowTemplate, FlowStep, KnowledgeBaseConfig, FlowTemplateRequest } from '../api/flowApi';
import { roleApi, Role } from '../api/roleApi';
import { knowledgeApi, KnowledgeBase } from '../api/knowledgeApi';

interface FlowTemplateCreatorProps {
  onClose: () => void;
  onSave: (template: FlowTemplate) => void;
  initialTemplate?: Partial<FlowTemplate>;
}

const FlowTemplateCreator: React.FC<FlowTemplateCreatorProps> = ({
  onClose,
  onSave,
  initialTemplate
}) => {
  const { theme } = useTheme();

  // Template basic info
  const [templateName, setTemplateName] = useState(initialTemplate?.name || '');
  const [templateTopic, setTemplateTopic] = useState(initialTemplate?.topic || '');
  const [templateType, setTemplateType] = useState<FlowTemplate['type']>(initialTemplate?.type || 'teaching');
  const [templateDescription, setTemplateDescription] = useState(initialTemplate?.description || '');

  // Roles and knowledge bases
  const [roles, setRoles] = useState<Role[]>([]);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [loadingRoles, setLoadingRoles] = useState(true);
  const [loadingKnowledgeBases, setLoadingKnowledgeBases] = useState(true);

  // Steps
  const [steps, setSteps] = useState<(FlowStep & { id: string; expanded: boolean })[]>(() => {
    if (initialTemplate?.steps) {
      return initialTemplate.steps.map((step, index) => ({
        ...step,
        id: `step-${Date.now()}-${index}`,
        expanded: false
      }));
    }
    return [{
      id: 'step-1',
      flow_template_id: 0,
      order: 1,
      speaker_role_ref: '',
      target_role_ref: '',
      task_type: 'ask_question',
      context_scope: 'last_message',
      context_param: {},
      logic_config: {},
      next_step_id: undefined,
      description: '',
      knowledge_base_config: {
        enabled: false,
        knowledge_base_ids: [],
        retrieval_params: {
          top_k: 5,
          similarity_threshold: 0.7,
          max_context_length: 2000
        }
      },
      expanded: true
    }];
  });

  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Load roles and knowledge bases
  useEffect(() => {
    const loadData = async () => {
      try {
        // Load roles
        const rolesResponse = await roleApi.getRoles({ page: 1, page_size: 100 });
        setRoles(rolesResponse.items);
        setLoadingRoles(false);

        // Load knowledge bases
        const kbResponse = await knowledgeApi.getKnowledgeBases({ page: 1, page_size: 100 });
        setKnowledgeBases(kbResponse.items);
        setLoadingKnowledgeBases(false);
      } catch (error) {
        console.error('Failed to load data:', error);
        setErrors(prev => ({ ...prev, general: 'Failed to load roles or knowledge bases' }));
        setLoadingRoles(false);
        setLoadingKnowledgeBases(false);
      }
    };

    loadData();
  }, []);

  // Step management
  const addStep = () => {
    const newStep: FlowStep & { id: string; expanded: boolean } = {
      id: `step-${Date.now()}`,
      flow_template_id: 0,
      order: steps.length + 1,
      speaker_role_ref: '',
      target_role_ref: '',
      task_type: 'ask_question',
      context_scope: 'last_message',
      context_param: {},
      logic_config: {},
      next_step_id: undefined,
      description: '',
      knowledge_base_config: {
        enabled: false,
        knowledge_base_ids: [],
        retrieval_params: {
          top_k: 5,
          similarity_threshold: 0.7,
          max_context_length: 2000
        }
      },
      expanded: true
    };
    setSteps([...steps, newStep]);
  };

  const removeStep = (stepId: string) => {
    setSteps(steps.filter(step => step.id !== stepId));
  };

  const toggleStepExpanded = (stepId: string) => {
    setSteps(steps.map(step =>
      step.id === stepId ? { ...step, expanded: !step.expanded } : step
    ));
  };

  const updateStep = (stepId: string, updates: Partial<FlowStep>) => {
    setSteps(steps.map(step =>
      step.id === stepId ? { ...step, ...updates } : step
    ));
  };

  const updateStepKnowledgeBaseConfig = (stepId: string, config: Partial<KnowledgeBaseConfig>) => {
    setSteps(steps.map(step =>
      step.id === stepId ? {
        ...step,
        knowledge_base_config: {
          ...step.knowledge_base_config,
          ...config
        }
      } : step
    ));
  };

  const toggleKnowledgeBaseSelection = (stepId: string, kbId: string) => {
    setSteps(steps.map(step => {
      if (step.id !== stepId) return step;

      const kbIds = step.knowledge_base_config?.knowledge_base_ids || [];
      const isSelected = kbIds.includes(kbId);

      return {
        ...step,
        knowledge_base_config: {
          ...step.knowledge_base_config,
          knowledge_base_ids: isSelected
            ? kbIds.filter(id => id !== kbId)
            : [...kbIds, kbId]
        }
      };
    }));
  };

  // Validation
  const validateTemplate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!templateName.trim()) {
      newErrors.name = 'Template name is required';
    }

    if (steps.length === 0) {
      newErrors.steps = 'At least one step is required';
    }

    steps.forEach((step, index) => {
      if (!step.speaker_role_ref) {
        newErrors[`step-${index}-speaker`] = 'Speaker role is required';
      }
      if (!step.task_type) {
        newErrors[`step-${index}-task`] = 'Task type is required';
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Save template
  const handleSave = async () => {
    if (!validateTemplate()) {
      return;
    }

    setSaving(true);
    try {
      const templateData: FlowTemplateRequest = {
        name: templateName,
        topic: templateTopic,
        type: templateType,
        description: templateDescription,
        is_active: true,
        steps: steps.map(({ id, flow_template_id, expanded, ...step }) => ({
          ...step,
          order: steps.findIndex(s => s.id === id) + 1
        }))
      };

      const savedTemplate = await flowApi.createFlow(templateData);
      onSave(savedTemplate);
    } catch (error) {
      console.error('Failed to save template:', error);
      setErrors(prev => ({ ...prev, general: 'Failed to save template' }));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900">
              {initialTemplate ? 'Edit Template' : 'Create New Template'}
            </h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {errors.general && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center">
                <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
                <span className="text-red-800">{errors.general}</span>
              </div>
            </div>
          )}

          {/* Basic Information */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Basic Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Template Name *
                </label>
                <input
                  type="text"
                  value={templateName}
                  onChange={(e) => setTemplateName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter template name"
                />
                {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Topic (Preset)
                </label>
                <input
                  type="text"
                  value={templateTopic}
                  onChange={(e) => setTemplateTopic(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter preset topic"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Template Type *
                </label>
                <select
                  value={templateType}
                  onChange={(e) => setTemplateType(e.target.value as FlowTemplate['type'])}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="teaching">Teaching</option>
                  <option value="review">Review</option>
                  <option value="debate">Debate</option>
                  <option value="discussion">Discussion</option>
                  <option value="interview">Interview</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  value={templateDescription}
                  onChange={(e) => setTemplateDescription(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Describe the template purpose and structure"
                />
              </div>
            </div>
          </div>

          {/* Steps */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Conversation Steps</h3>
              <button
                onClick={addStep}
                className={`inline-flex items-center px-3 py-2 text-sm font-medium text-white rounded-lg ${theme.primary} ${theme.primaryHover} transition-colors`}
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Step
              </button>
            </div>

            {errors.steps && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-800">{errors.steps}</p>
              </div>
            )}

            <div className="space-y-4">
              {steps.map((step, index) => (
                <div key={step.id} className="border border-gray-200 rounded-lg">
                  {/* Step Header */}
                  <div
                    className="p-4 bg-gray-50 cursor-pointer flex items-center justify-between"
                    onClick={() => toggleStepExpanded(step.id)}
                  >
                    <div className="flex items-center space-x-3">
                      <div className={`w-8 h-8 rounded-full ${theme.iconBg} bg-opacity-10 flex items-center justify-center`}>
                        <span className="text-sm font-medium">{index + 1}</span>
                      </div>
                      <div>
                        <h4 className="font-medium text-gray-900">
                          {step.speaker_role_ref ? `Role: ${step.speaker_role_ref}` : 'Step ' + (index + 1)}
                        </h4>
                        <p className="text-sm text-gray-600">
                          {step.task_type.replace('_', ' ')} → {step.target_role_ref || 'Next'}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {step.knowledge_base_config?.enabled && (
                        <Database className="w-4 h-4 text-blue-500" />
                      )}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          removeStep(step.id);
                        }}
                        className="p-1 hover:bg-red-100 rounded transition-colors"
                      >
                        <Trash2 className="w-4 h-4 text-red-500" />
                      </button>
                      <div className="transform transition-transform">
                        {step.expanded ? (
                          <ChevronUp className="w-5 h-5 text-gray-400" />
                        ) : (
                          <ChevronDown className="w-5 h-5 text-gray-400" />
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Step Details */}
                  {step.expanded && (
                    <div className="p-4 border-t border-gray-200">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Speaker Role *
                          </label>
                          <select
                            value={step.speaker_role_ref}
                            onChange={(e) => updateStep(step.id, { speaker_role_ref: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          >
                            <option value="">Select speaker role</option>
                            {roles.map((role) => (
                              <option key={role.id} value={role.name}>
                                {role.name}
                              </option>
                            ))}
                          </select>
                          {errors[`step-${index}-speaker`] && (
                            <p className="text-red-500 text-sm mt-1">{errors[`step-${index}-speaker`]}</p>
                          )}
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Target Role
                          </label>
                          <select
                            value={step.target_role_ref || ''}
                            onChange={(e) => updateStep(step.id, { target_role_ref: e.target.value || undefined })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          >
                            <option value="">Select target role (optional)</option>
                            {roles.map((role) => (
                              <option key={role.id} value={role.name}>
                                {role.name}
                              </option>
                            ))}
                          </select>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Task Type *
                          </label>
                          <select
                            value={step.task_type}
                            onChange={(e) => updateStep(step.id, { task_type: e.target.value as any })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          >
                            <option value="ask_question">Ask Question</option>
                            <option value="answer_question">Answer Question</option>
                            <option value="review_answer">Review Answer</option>
                            <option value="question">Question</option>
                            <option value="summarize">Summarize</option>
                            <option value="evaluate">Evaluate</option>
                            <option value="suggest">Suggest</option>
                            <option value="challenge">Challenge</option>
                            <option value="support">Support</option>
                            <option value="conclude">Conclude</option>
                          </select>
                          {errors[`step-${index}-task`] && (
                            <p className="text-red-500 text-sm mt-1">{errors[`step-${index}-task`]}</p>
                          )}
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Context Scope
                          </label>
                          <select
                            value={step.context_scope as string}
                            onChange={(e) => updateStep(step.id, { context_scope: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          >
                            <option value="none">None</option>
                            <option value="last_message">Last Message</option>
                            <option value="last_round">Last Round</option>
                            <option value="all">All Messages</option>
                          </select>
                        </div>
                      </div>

                      <div className="mb-4">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Description
                        </label>
                        <textarea
                          value={step.description || ''}
                          onChange={(e) => updateStep(step.id, { description: e.target.value })}
                          rows={2}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          placeholder="Describe what this step should accomplish"
                        />
                      </div>

                      {/* Knowledge Base Configuration */}
                      <div className="border-t border-gray-200 pt-4">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center">
                            <Database className="w-5 h-5 text-gray-600 mr-2" />
                            <h4 className="text-sm font-medium text-gray-900">Knowledge Base Configuration</h4>
                          </div>
                          <button
                            onClick={() => updateStepKnowledgeBaseConfig(step.id, {
                              enabled: !step.knowledge_base_config?.enabled
                            })}
                            className={`px-3 py-1 text-xs font-medium rounded-full ${
                              step.knowledge_base_config?.enabled
                                ? 'bg-green-100 text-green-800'
                                : 'bg-gray-100 text-gray-600'
                            }`}
                          >
                            {step.knowledge_base_config?.enabled ? 'Enabled' : 'Disabled'}
                          </button>
                        </div>

                        {step.knowledge_base_config?.enabled && (
                          <div className="space-y-3">
                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-2">
                                Select Knowledge Bases
                              </label>
                              {loadingKnowledgeBases ? (
                                <div className="flex items-center justify-center py-4">
                                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
                                </div>
                              ) : knowledgeBases.length === 0 ? (
                                <p className="text-gray-500 text-sm">No knowledge bases available</p>
                              ) : (
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-32 overflow-y-auto">
                                  {knowledgeBases.map((kb) => (
                                    <label
                                      key={kb.id}
                                      className="flex items-center p-2 border border-gray-200 rounded hover:bg-gray-50 cursor-pointer"
                                    >
                                      <input
                                        type="checkbox"
                                        checked={step.knowledge_base_config?.knowledge_base_ids?.includes(kb.id.toString()) || false}
                                        onChange={() => toggleKnowledgeBaseSelection(step.id, kb.id.toString())}
                                        className="mr-2 rounded text-blue-500 focus:ring-blue-500"
                                      />
                                      <div>
                                        <div className="text-sm font-medium text-gray-900">{kb.name}</div>
                                        <div className="text-xs text-gray-500">
                                          {kb.document_count || 0} documents
                                        </div>
                                      </div>
                                    </label>
                                  ))}
                                </div>
                              )}
                            </div>

                            <div className="grid grid-cols-3 gap-4">
                              <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                  Top K Results
                                </label>
                                <input
                                  type="number"
                                  min="1"
                                  max="20"
                                  value={step.knowledge_base_config?.retrieval_params?.top_k || 5}
                                  onChange={(e) => updateStepKnowledgeBaseConfig(step.id, {
                                    retrieval_params: {
                                      ...step.knowledge_base_config?.retrieval_params,
                                      top_k: parseInt(e.target.value) || 5
                                    }
                                  })}
                                  className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                                />
                              </div>

                              <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                  Similarity Threshold
                                </label>
                                <input
                                  type="number"
                                  min="0"
                                  max="1"
                                  step="0.1"
                                  value={step.knowledge_base_config?.retrieval_params?.similarity_threshold || 0.7}
                                  onChange={(e) => updateStepKnowledgeBaseConfig(step.id, {
                                    retrieval_params: {
                                      ...step.knowledge_base_config?.retrieval_params,
                                      similarity_threshold: parseFloat(e.target.value) || 0.7
                                    }
                                  })}
                                  className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                                />
                              </div>

                              <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                  Max Context Length
                                </label>
                                <input
                                  type="number"
                                  min="100"
                                  max="8000"
                                  step="100"
                                  value={step.knowledge_base_config?.retrieval_params?.max_context_length || 2000}
                                  onChange={(e) => updateStepKnowledgeBaseConfig(step.id, {
                                    retrieval_params: {
                                      ...step.knowledge_base_config?.retrieval_params,
                                      max_context_length: parseInt(e.target.value) || 2000
                                    }
                                  })}
                                  className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                                />
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600">
              {steps.length} step{steps.length !== 1 ? 's' : ''} configured
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={onClose}
                className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                disabled={saving}
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving || !templateName.trim() || steps.length === 0}
                className={`px-4 py-2 text-white rounded-lg ${theme.primary} ${theme.primaryHover} transition-colors disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {saving ? 'Saving...' : 'Save Template'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FlowTemplateCreator;