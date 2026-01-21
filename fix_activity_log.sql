-- Script SQL para arreglar la tabla activity_log
-- Elimina las columnas de backup que fueron agregadas por error

-- Verificar columnas actuales
SHOW COLUMNS FROM activity_log;

-- Eliminar columnas problemáticas
ALTER TABLE activity_log DROP COLUMN IF EXISTS backup_path;
ALTER TABLE activity_log DROP COLUMN IF EXISTS file_size;
ALTER TABLE activity_log DROP COLUMN IF EXISTS success;
ALTER TABLE activity_log DROP COLUMN IF EXISTS error_message;

-- Verificar que se eliminaron
SHOW COLUMNS FROM activity_log;
