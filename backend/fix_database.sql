-- Add missing knowledge_base_config column to flow_steps table
ALTER TABLE flow_steps ADD COLUMN _knowledge_base_config TEXT;