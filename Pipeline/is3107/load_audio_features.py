from .connect_to_bigquery import connect_to_bigquery_op
from .config_schema_audio_features import config_schema_audio_features_op
# from .duplicates_table import create_duplicates_table_op
from google.cloud import bigquery

def load_audio_features_op(clean_audio_features):
    client = connect_to_bigquery_op()
    schema, job_config = config_schema_audio_features_op()
    table_id = "snappy-boulder-378707.NewReleases.NewAudioFeatures"
    table_id_dup = "snappy-boulder-378707.NewReleases.NewAudioFeaturesDuplicates"

    # create_duplicates_table_op(config_schema_audio_features_op, table_id_dup)

    table = client.get_table(table_id)
    original_rows = table.num_rows
    print("Total rows in table: ", original_rows)

    # Load Audio Features
    if original_rows == 0:
        job_config.write_disposition = bigquery.WriteDisposition.WRITE_TRUNCATE
    else:
        job_config.write_disposition = bigquery.WriteDisposition.WRITE_APPEND
        
    job = client.load_table_from_dataframe(clean_audio_features, table_id, job_config=job_config)
    job.result()  # Waits for the job to complete.
    table = client.get_table(table_id)  # Make an API request.
    rows_after_loading = table.num_rows

    print(
        "Loaded {} rows and {} columns to {}".format(
            (rows_after_loading - original_rows), len(table.schema), table_id
        )
    )
    print("Total rows in table after loading: ", rows_after_loading)

    # # Load duplicates into a duplicate table
    # identify_duplicates = client.query("""
    #     INSERT INTO snappy-boulder-378707.NewReleases.NewAudioFeaturesDuplicates
    #     WITH first_row AS (
    #         SELECT ROW_NUMBER() OVER (PARTITION BY id) AS row_number, *
    #         FROM snappy-boulder-378707.NewReleases.NewAudioFeatures
    #     )
    #     SELECT id, danceability, energy, key, loudness, mode, speechiness, acousticness, instrumentalness, liveness, valence, tempo, duration_ms, time_signature
    #     FROM first_row
    #     WHERE row_number = 1
    # """)
    # identify_duplicates.result()
    # table = client.get_table(table_id_dup)
    # rows_dup = table.num_rows
    # print("Total rows in duplicates table: ", rows_dup)

    # # Delete all duplicate records in the orginial table
    # delete_duplicates = client.query("""
    #     DELETE FROM snappy-boulder-378707.NewReleases.NewAudioFeatures
    #     WHERE id
    #     IN (SELECT DISTINCT id FROM snappy-boulder-378707.NewReleases.NewAudioFeaturesDuplicates)
    # """)
    # delete_duplicates.result()
    # table = client.get_table(table_id)
    # rows_after_deletion = table.num_rows
    # print("Total rows deleted in table: ", rows_after_loading - rows_after_deletion)
    # print("Total rows in table after deleting duplicates: ", rows_after_deletion)

    # # Insert one copy of every duplicate record back
    # insert_back = client.query("""
    #     INSERT INTO snappy-boulder-378707.NewReleases.NewAudioFeatures
    #     SELECT * FROM snappy-boulder-378707.NewReleases.NewAudioFeaturesDuplicates
    # """)
    # insert_back.result()
    # table = client.get_table(table_id)
    # rows_after_inserting_back = table.num_rows
    # print("Total rows in table after inserting back: ", rows_after_inserting_back)
    
    # # Delete records in the duplicate table
    # table = client.get_table(table_id_dup)
    # rows_dup = table.num_rows
    # delete_records_in_duplicates_table = client.query("""
    #     TRUNCATE TABLE snappy-boulder-378707.NewReleases.NewAudioFeaturesDuplicates
    # """)
    # delete_records_in_duplicates_table.result()
    # table = client.get_table(table_id_dup)
    # rows_after_deletion_dup = table.num_rows
    # print("Total rows deleted in duplicates table: ", rows_dup - rows_after_deletion_dup)

    return
