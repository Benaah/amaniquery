---
description: Database Backup and Restore
---

# Database Backup and Restore Workflow

This workflow provides instructions for backing up and restoring the PostgreSQL database in both Docker and Kubernetes environments.

## Docker Environments

1. Backup the PostgreSQL database to a timestamped `.sql` file:
   // turbo

   ```bash
   make db-backup
   ```

2. Check the size and contents of the generated backup file (e.g., `backup_2026...sql`):

   ```bash
   ls -lh backup_*.sql
   ```

3. To restore the PostgreSQL database from a specific `.sql` backup file (replace `YOUR_BACKUP_FILE.sql` with the actual filename):

   ```bash
   make db-restore FILE=YOUR_BACKUP_FILE.sql
   ```

## Kubernetes Environments

1. Create a backup of the PostgreSQL database in the running cluster:
   // turbo

   ```bash
   make k8s-db-backup
   ```

2. The file will be saved locally as `backup_k8s_...sql`. Check its size:

   ```bash
   ls -lh backup_k8s_*.sql
   ```

3. To restore the database manually inside the cluster, first copy the backup inside the pod, then restore:

   ```bash
   kubectl cp YOUR_BACKUP_FILE.sql amaniquery/postgres-0:/tmp/backup.sql
   kubectl exec -it -n amaniquery postgres-0 -- psql -U amaniquery -d amaniquery -f /tmp/backup.sql
   ```

## Vector Database Maintenance

1. If ChromaDB data is corrupted, clear the volume/data directory (WARNING: deleting data):

   ```bash
   # Local dev data directory
   rm -rf data/embeddings/chroma_db
   ```

2. Repopulate the database using the population script:

   ```bash
   python -m Module3_NiruDB.populate_db
   ```
