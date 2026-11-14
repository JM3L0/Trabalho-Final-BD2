-- Parte 2.4: Backup nativo de Ecommerce_Baseline e restauracao como Ecommerce_Otimizado
USE [master];
GO

BACKUP DATABASE [Ecommerce_Baseline]
TO DISK = N'/var/opt/mssql/data_import/ecommerce_init.bak'
WITH FORMAT, INIT, COMPRESSION, NAME = N'Ecommerce_Baseline-Full';
GO

IF DB_ID(N'Ecommerce_Otimizado') IS NOT NULL
BEGIN
    ALTER DATABASE [Ecommerce_Otimizado] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
END;
GO

RESTORE DATABASE [Ecommerce_Otimizado]
FROM DISK = N'/var/opt/mssql/data_import/ecommerce_init.bak'
WITH REPLACE,
     MOVE N'Ecommerce_Baseline'     TO N'/var/opt/mssql/data/Ecommerce_Otimizado.mdf',
     MOVE N'Ecommerce_Baseline_log' TO N'/var/opt/mssql/data/Ecommerce_Otimizado_log.ldf';
GO

ALTER DATABASE [Ecommerce_Otimizado] SET MULTI_USER;
ALTER DATABASE [Ecommerce_Otimizado] SET RECOVERY SIMPLE;
GO

USE [Ecommerce_Otimizado];
GO
CHECKPOINT;
DBCC SHRINKFILE (N'Ecommerce_Baseline_log', 64);
GO
