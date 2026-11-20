import os
import sys
from dotenv import load_dotenv
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

# Load backend/.env
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

account_id = os.getenv("R2_ACCOUNT_ID")
access_key = os.getenv("R2_ACCESS_KEY_ID")
secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
bucket_name = os.getenv("R2_BUCKET_NAME", "gurudok-staging-buket")

print("=" * 60)
print("TEST KONEKSI CLOUDFLARE R2 (S3 API)")
print("=" * 60)
print(f"Bucket Name : {bucket_name}")
print(f"Account ID  : {account_id}")
print(f"Access Key  : {'Terisi (***' + access_key[-4:] + ')' if access_key else 'BELUM DIISI'}")
print(f"Secret Key  : {'Terisi (Panjang: ' + str(len(secret_key)) + ' Karakter)' if secret_key else 'BELUM DIISI'}")
print("-" * 60)

if not access_key or not secret_key or not account_id:
    print("❌ KONEKSI GAGAL: Kredensial belum lengkap di backend/.env.")
    print("Silakan masukkan R2_ACCESS_KEY_ID dan R2_SECRET_ACCESS_KEY terlebih dahulu.")
    sys.exit(1)

endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"
print(f"Connecting to Endpoint: {endpoint_url} ...")

try:
    s3 = boto3.client(
        service_name="s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )

    # 1. Test Head Bucket
    print(f"1. Memeriksa keberadaan bucket '{bucket_name}'...")
    s3.head_bucket(Bucket=bucket_name)
    print("   ✅ Bucket terdeteksi dan dapat diakses!")

    # 2. Test Put Object (Upload)
    test_key = "system_test_connection.txt"
    test_bytes = b"GuruDok Cloudflare R2 Connection Test: SUCCESS!"
    print(f"2. Menguji Upload berkas '{test_key}'...")
    s3.put_object(
        Bucket=bucket_name,
        Key=test_key,
        Body=test_bytes,
        ContentType="text/plain",
    )
    print("   ✅ Upload berhasil!")

    # 3. Test Get Object (Download)
    print(f"3. Menguji Download berkas '{test_key}'...")
    resp = s3.get_object(Bucket=bucket_name, Key=test_key)
    downloaded = resp["Body"].read()
    assert downloaded == test_bytes, "Data integritas tidak cocok!"
    print(f"   ✅ Download berhasil! Isi: '{downloaded.decode()}'")

    # 4. Test Cleanup (Delete)
    print(f"4. Membersihkan berkas uji coba...")
    s3.delete_object(Bucket=bucket_name, Key=test_key)
    print("   ✅ Pembersihan selesai!")

    print("-" * 60)
    print("🎉 STATUS: 100% KONEKSI LIVE CLOUDFLARE R2 SUKSES & VALID!")
    print("=" * 60)

except ClientError as e:
    print(f"❌ ERROR CLOUDFLARE R2: {str(e)}")
    sys.exit(1)
except Exception as exc:
    print(f"❌ ERROR: {str(exc)}")
    sys.exit(1)
