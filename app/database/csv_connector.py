from typing import List, Dict, Any, Optional, Iterator, AsyncGenerator
import pandas as pd
import json
import logging
from datetime import datetime
from pathlib import Path
from ..database.base import DatabaseConnector
from ..models import CSVConfig, CSVColumnType, CSVColumnConfig

logger = logging.getLogger(__name__)

class CSVConnector(DatabaseConnector):
    """Database connector for CSV files."""
    
    def __init__(self, csv_config: CSVConfig):
        """
        Initialize CSV connector.
        
        Args:
            csv_config: CSV configuration containing file path and column definitions
        """
        self.csv_config = csv_config
        self.df: Optional[pd.DataFrame] = None
        self._validate_config()
        
    def _validate_config(self) -> None:
        """Validate CSV configuration."""
        # Check if file exists
        if not Path(self.csv_config.file_path).exists():
            raise FileNotFoundError(f"CSV file not found: {self.csv_config.file_path}")
            
        # Validate text columns exist in column definitions
        column_names = [col.name for col in self.csv_config.columns]
        for text_col in self.csv_config.text_columns:
            if text_col not in column_names:
                raise ValueError(f"Text column '{text_col}' not found in column definitions")
                
        # Validate metadata columns if specified
        if self.csv_config.metadata_columns:
            for meta_col in self.csv_config.metadata_columns:
                if meta_col not in column_names:
                    raise ValueError(f"Metadata column '{meta_col}' not found in column definitions")
    
    async def connect(self) -> None:
        """Load and process CSV file."""
        try:
            logger.info(f"Loading CSV file: {self.csv_config.file_path}")
            
            # Read CSV file
            read_params = {
                'filepath_or_buffer': self.csv_config.file_path,
                'delimiter': self.csv_config.delimiter,
                'encoding': self.csv_config.encoding,
                'skiprows': self.csv_config.skip_rows
            }
            
            if not self.csv_config.has_header:
                read_params['header'] = None
                read_params['names'] = [col.name for col in self.csv_config.columns]
            
            if self.csv_config.max_rows:
                read_params['nrows'] = self.csv_config.max_rows
                
            self.df = pd.read_csv(**read_params)
            
            # Process and validate data
            await self._process_dataframe()
            
            logger.info(f"Successfully loaded CSV with {len(self.df)} rows and {len(self.df.columns)} columns")
            
        except Exception as e:
            logger.error(f"Failed to load CSV file: {e}")
            raise
    
    async def _process_dataframe(self) -> None:
        """Process and clean the dataframe according to column configurations."""
        if self.df is None:
            raise ValueError("DataFrame not loaded")
            
        # Create column mapping for processing
        column_configs = {col.name: col for col in self.csv_config.columns}
        
        for column_name in self.df.columns:
            if column_name in column_configs:
                col_config = column_configs[column_name]
                await self._process_column(column_name, col_config)
            else:
                logger.warning(f"Column '{column_name}' found in CSV but not in configuration")
        
        # Handle missing required columns
        for col_config in self.csv_config.columns:
            if col_config.required and col_config.name not in self.df.columns:
                if col_config.default_value is not None:
                    self.df[col_config.name] = col_config.default_value
                    logger.info(f"Added missing required column '{col_config.name}' with default value")
                else:
                    raise ValueError(f"Required column '{col_config.name}' missing and no default value provided")
    
    async def _process_column(self, column_name: str, config: CSVColumnConfig) -> None:
        """Process individual column according to its configuration."""
        try:
            if config.type == CSVColumnType.TEXT:
                # Ensure text columns are strings and handle NaN
                self.df[column_name] = self.df[column_name].astype(str).replace('nan', '')
                
            elif config.type == CSVColumnType.INTEGER:
                # Convert to integer, handling NaN
                self.df[column_name] = pd.to_numeric(self.df[column_name], errors='coerce').fillna(0).astype(int)
                
            elif config.type == CSVColumnType.FLOAT:
                # Convert to float, handling NaN
                self.df[column_name] = pd.to_numeric(self.df[column_name], errors='coerce').fillna(0.0)
                
            elif config.type == CSVColumnType.DATETIME:
                # Convert to datetime
                self.df[column_name] = pd.to_datetime(self.df[column_name], errors='coerce')
                
            elif config.type == CSVColumnType.BOOLEAN:
                # Convert to boolean
                self.df[column_name] = self.df[column_name].astype(str).str.lower().isin(['true', '1', 'yes', 'y'])
                
            elif config.type == CSVColumnType.JSON:
                # Parse JSON strings
                def safe_json_parse(value):
                    try:
                        if pd.isna(value) or value == '':
                            return {}
                        return json.loads(str(value))
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in column '{column_name}': {value}")
                        return {}
                
                self.df[column_name] = self.df[column_name].apply(safe_json_parse)
                
        except Exception as e:
            logger.error(f"Error processing column '{column_name}': {e}")
            # Fill with default value if processing fails
            if config.default_value is not None:
                self.df[column_name] = config.default_value
            else:
                raise
    
    async def disconnect(self) -> None:
        """Clean up resources."""
        self.df = None
        logger.info("CSV connector disconnected")
    
    async def fetch_data(
        self,
        table_or_collection: str,
        columns: List[str] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Fetch data from the CSV.
        
        Args:
            table_or_collection: Ignored for CSV (single file)
            columns: Specific columns to fetch
            limit: Maximum number of rows to return
            offset: Number of rows to skip
            
        Returns:
            List of dictionaries representing rows
        """
        if self.df is None:
            raise ValueError("CSV not loaded. Call connect() first.")
        
        # Create working dataframe
        working_df = self.df.copy()
        
        # Select specific columns if requested
        if columns:
            available_columns = [col for col in columns if col in working_df.columns]
            if not available_columns:
                logger.warning("No requested columns found in CSV")
                return []
            working_df = working_df[available_columns]
        
        # Apply offset and limit
        if offset > 0:
            working_df = working_df.iloc[offset:]
        if limit:
            working_df = working_df.head(limit)
        
        # Convert to list of dictionaries
        records = working_df.to_dict('records')
        
        # Clean up records (convert NaN to None, etc.)
        cleaned_records = []
        for record in records:
            cleaned_record = {}
            for key, value in record.items():
                if pd.isna(value):
                    cleaned_record[key] = None
                elif isinstance(value, pd.Timestamp):
                    cleaned_record[key] = value.isoformat()
                else:
                    cleaned_record[key] = value
            cleaned_records.append(cleaned_record)
        
        logger.info(f"Fetched {len(cleaned_records)} records from CSV")
        return cleaned_records
    
    async def disconnect(self) -> None:
        """Close CSV connector (no-op for CSV files)."""
        logger.info("CSV connector closed")
        
    async def test_connection(self) -> bool:
        """Test if the CSV file can be read."""
        try:
            if not Path(self.csv_config.file_path).exists():
                return False
            # Try to read first few rows to test accessibility
            pd.read_csv(self.csv_config.file_path, nrows=1)
            return True
        except Exception as e:
            logger.error(f"CSV connection test failed: {e}")
            return False
            
    async def get_schema(self, table_or_collection: str) -> Dict[str, str]:
        """Get schema information for CSV columns."""
        schema = {}
        for column in self.csv_config.columns:
            schema[column.name] = column.type.value
        return schema
    
    async def get_data(
        self, 
        table_or_collection: str, 
        columns_or_fields: List[str], 
        limit: int = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Get data from CSV file."""
        if self.df is None:
            await self.connect()
            
        # Filter columns if specified
        if columns_or_fields:
            available_columns = [col for col in columns_or_fields if col in self.df.columns]
            if available_columns:
                df_subset = self.df[available_columns]
            else:
                df_subset = self.df
        else:
            df_subset = self.df
            
        # Apply limit if specified
        if limit:
            df_subset = df_subset.head(limit)
            
        # Yield records one by one
        for _, row in df_subset.iterrows():
            yield row.to_dict()

    def get_text_content(self, record: Dict[str, Any]) -> str:
        """
        Extract text content for embedding from a record.
        
        Args:
            record: Data record
            
        Returns:
            Combined text content from configured text columns
        """
        text_parts = []
        for column in self.csv_config.text_columns:
            if column in record and record[column] is not None:
                text_content = str(record[column]).strip()
                if text_content:
                    text_parts.append(text_content)
        
        return " ".join(text_parts)
    
    def get_metadata(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from a record.
        
        Args:
            record: Data record
            
        Returns:
            Metadata dictionary
        """
        metadata = {
            "source": "csv",
            "file_path": str(self.csv_config.file_path)
        }
        
        # Add configured metadata columns
        if self.csv_config.metadata_columns:
            for column in self.csv_config.metadata_columns:
                if column in record:
                    metadata[column] = record[column]
        
        # Add row index if available
        if 'index' in record:
            metadata['row_index'] = record['index']
            
        return metadata
    
    async def fetch_in_chunks(self, chunk_size: Optional[int] = None) -> AsyncGenerator[List[Dict[str, Any]], None]:
        """
        Fetch data in chunks for memory-efficient processing.
        
        Args:
            chunk_size: Size of each chunk (uses config default if not provided)
            
        Yields:
            Chunks of data as list of dictionaries
        """
        if self.df is None:
            raise ValueError("CSV not loaded. Call connect() first.")
        
        chunk_size = chunk_size or self.csv_config.chunk_size
        total_rows = len(self.df)
        
        for start_idx in range(0, total_rows, chunk_size):
            end_idx = min(start_idx + chunk_size, total_rows)
            chunk_df = self.df.iloc[start_idx:end_idx]
            
            # Convert chunk to records
            records = chunk_df.to_dict('records')
            
            # Clean up records
            cleaned_records = []
            for record in records:
                cleaned_record = {}
                for key, value in record.items():
                    if pd.isna(value):
                        cleaned_record[key] = None
                    elif isinstance(value, pd.Timestamp):
                        cleaned_record[key] = value.isoformat()
                    else:
                        cleaned_record[key] = value
                cleaned_records.append(cleaned_record)
            
            logger.debug(f"Yielding chunk {start_idx}-{end_idx} with {len(cleaned_records)} records")
            yield cleaned_records
    
    def get_schema_info(self) -> Dict[str, Any]:
        """
        Get information about the CSV schema.
        
        Returns:
            Dictionary containing schema information
        """
        if self.df is None:
            return {"error": "CSV not loaded"}
        
        schema_info = {
            "file_path": str(self.csv_config.file_path),
            "total_rows": len(self.df),
            "total_columns": len(self.df.columns),
            "columns": {}
        }
        
        # Add column information
        for column in self.df.columns:
            col_config = next((c for c in self.csv_config.columns if c.name == column), None)
            schema_info["columns"][column] = {
                "dtype": str(self.df[column].dtype),
                "non_null_count": int(self.df[column].count()),
                "null_count": int(self.df[column].isnull().sum()),
                "configured_type": col_config.type if col_config else "unknown",
                "is_text_column": column in self.csv_config.text_columns,
                "is_metadata_column": column in (self.csv_config.metadata_columns or [])
            }
        
        return schema_info
