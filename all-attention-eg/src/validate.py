#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil
from pathlib import Path
from PIL import Image, ImageFile
import magic  # requires: pip install python-magic

# Allow loading truncated images
ImageFile.LOAD_TRUNCATED_IMAGES = True


def check_file_type(file_path):
    """Check the actual file type using libmagic"""
    mime = magic.Magic(mime=True)
    file_type = mime.from_file(file_path)
    return file_type


def run_command(cmd):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), -1


def diagnose_and_fix_images(directory):
    """
    Advanced diagnosis and repair of image files
    """
    print(f"Analyzing images in: {directory}")

    # Create directories for different operations
    repair_dir = os.path.join(directory, "repaired")
    os.makedirs(repair_dir, exist_ok=True)

    # Get all files with image-like extensions
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
    all_files = [f for f in os.listdir(directory)
                 if os.path.isfile(os.path.join(directory, f)) and
                 os.path.splitext(f.lower())[1] in image_extensions]

    report = []

    for i, filename in enumerate(all_files):
        file_path = os.path.join(directory, filename)
        file_size = os.path.getsize(file_path)
        base_name, ext = os.path.splitext(filename)

        print(f"Analyzing {i + 1}/{len(all_files)}: {filename} ({file_size} bytes)")

        # Check actual file type with libmagic
        file_type = check_file_type(file_path)
        print(f"  Detected MIME type: {file_type}")

        # Skip zero-sized files
        if file_size == 0:
            result = f"SKIP: Zero-sized file"
            report.append((filename, "zero-size", "", result))
            continue

        # First try to open with PIL
        try:
            with Image.open(file_path) as img:
                img.verify()
                width, height = Image.open(file_path).size
                result = f"OK: Valid image ({width}x{height})"
                report.append((filename, file_type, "", result))
                print(f"  {result}")
                continue
        except Exception as e:
            error_message = str(e)
            print(f"  PIL Error: {error_message}")

            # Analyze with file command for more details
            stdout, stderr, _ = run_command(["file", file_path])
            print(f"  File command says: {stdout.strip()}")

            # Try different repair methods
            repair_methods = []

            # Method 1: If it's a PNG file, try pngcheck
            if ext.lower() == '.png' or file_type.startswith('image/png'):
                stdout, stderr, _ = run_command(["pngcheck", "-v", file_path])
                print(f"  PNG Check: {stderr.strip() if stderr else stdout.strip()}")
                repair_methods.append(('pngcheck', stderr or stdout))

            # Method 2: Force-convert with ImageMagick
            new_path = os.path.join(repair_dir, f"{base_name}_repaired{ext}")
            stdout, stderr, rc = run_command(["convert", file_path, "-strip", new_path])

            if rc == 0 and os.path.exists(new_path) and os.path.getsize(new_path) > 0:
                try:
                    with Image.open(new_path) as img:
                        width, height = img.size
                        result = f"FIXED: Converted with ImageMagick ({width}x{height})"
                        print(f"  {result}")
                        repair_methods.append(('imagemagick', result))
                except Exception as e:
                    os.remove(new_path) if os.path.exists(new_path) else None
                    repair_methods.append(('imagemagick', f"Failed: {str(e)}"))
            else:
                repair_methods.append(('imagemagick', f"Failed: {stderr or stdout}"))

            # Method 3: Try using a different extension
            for test_ext in ['.jpg', '.png']:
                if test_ext.lower() != ext.lower():
                    new_test_path = os.path.join(repair_dir, f"{base_name}_changed{test_ext}")
                    stdout, stderr, rc = run_command(["convert", file_path, new_test_path])

                    if rc == 0 and os.path.exists(new_test_path) and os.path.getsize(new_test_path) > 0:
                        try:
                            with Image.open(new_test_path) as img:
                                width, height = img.size
                                result = f"FIXED: Changed extension to {test_ext} ({width}x{height})"
                                print(f"  {result}")
                                repair_methods.append(('extension-change', result))
                                break
                        except Exception as e:
                            os.remove(new_test_path) if os.path.exists(new_test_path) else None
                            repair_methods.append(('extension-change', f"Failed with {test_ext}: {str(e)}"))
                    else:
                        repair_methods.append(('extension-change', f"Failed with {test_ext}: {stderr or stdout}"))

            # Method 4: If the file is suspiciously empty or malformed, check if it's a text file
            if file_size < 1000 or file_type.startswith('text/'):
                with open(file_path, 'rb') as f:
                    content = f.read(1000)
                    try:
                        text = content.decode('utf-8', errors='ignore')
                        print(f"  First 100 characters: {text[:100]}")
                        repair_methods.append(('content-snippet', text[:100]))
                    except Exception:
                        repair_methods.append(('content-snippet', "Binary data"))

            # Report the failed file
            report.append((filename, file_type, error_message,
                           "FAILED: " + "; ".join([f"{m[0]}: {m[1]}" for m in repair_methods])))

    # Print summary report
    print("\n==== SUMMARY REPORT ====")
    valid = [r for r in report if r[3].startswith("OK")]
    fixed = [r for r in report if r[3].startswith("FIXED")]
    failed = [r for r in report if r[3].startswith("FAILED")]

    print(f"Total files: {len(report)}")
    print(f"Valid files: {len(valid)}")
    print(f"Fixed files: {len(fixed)}")
    print(f"Failed files: {len(failed)}")

    if fixed:
        print("\n== Successfully Fixed Files ==")
        for f in fixed:
            print(f"{f[0]}: {f[3]}")

    if failed:
        print("\n== Files That Could Not Be Fixed ==")
        for f in failed:
            print(f"{f[0]}: {f[1]} - {f[2]}")

    print("\n== Suggestions ==")
    print("1. For all fixed files, check the 'repaired' directory and verify the images look correct")
    print("2. For failed files, consider:")
    print("   - Recreating or re-downloading the original images")
    print("   - Checking if the file extensions match the actual content type")
    print("   - Using specialized repair tools for specific formats")

    # Write report to file
    report_path = os.path.join(directory, "image_repair_report.txt")
    with open(report_path, 'w') as f:
        f.write("Image Repair Report\n")
        f.write("==================\n\n")

        f.write("Summary:\n")
        f.write(f"- Total files: {len(report)}\n")
        f.write(f"- Valid files: {len(valid)}\n")
        f.write(f"- Fixed files: {len(fixed)}\n")
        f.write(f"- Failed files: {len(failed)}\n\n")

        f.write("Detailed Results:\n")
        for filename, file_type, error, result in report:
            f.write(f"{filename}\n")
            f.write(f"  Type: {file_type}\n")
            f.write(f"  Error: {error}\n") if error else None
            f.write(f"  Result: {result}\n\n")

    print(f"\nDetailed report saved to {report_path}")
    return report


def create_filtered_dataset(directory, valid_only=True):
    """Create a filtered dataset with only valid images"""
    source_dir = directory
    target_dir = os.path.join(directory, "filtered_dataset")
    os.makedirs(target_dir, exist_ok=True)

    count = 0
    print(f"\nCreating filtered dataset in {target_dir}")

    # Get all files with common image extensions
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
    all_files = [f for f in os.listdir(source_dir)
                 if os.path.isfile(os.path.join(source_dir, f)) and
                 os.path.splitext(f.lower())[1] in image_extensions]

    for filename in all_files:
        file_path = os.path.join(source_dir, filename)

        try:
            # Only copy valid images
            with Image.open(file_path) as img:
                img.verify()
                # Make a clean copy to the filtered dataset
                target_path = os.path.join(target_dir, filename)
                shutil.copy2(file_path, target_path)
                count += 1
        except Exception:
            # Skip invalid images
            pass

    # Also check repaired directory if not valid_only
    if not valid_only and os.path.exists(os.path.join(source_dir, "repaired")):
        repaired_dir = os.path.join(source_dir, "repaired")
        for filename in os.listdir(repaired_dir):
            file_path = os.path.join(repaired_dir, filename)
            if not os.path.isfile(file_path):
                continue

            try:
                # Verify it's a valid image
                with Image.open(file_path) as img:
                    img.verify()
                    # Copy to filtered dataset
                    target_path = os.path.join(target_dir, filename)
                    shutil.copy2(file_path, target_path)
                    count += 1
            except Exception:
                # Skip invalid repaired images
                pass

    print(f"Created filtered dataset with {count} valid images")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = input("Enter the directory path containing your images: ")

    # Install dependencies if not already installed
    try:
        import magic
    except ImportError:
        print("Installing required python-magic library...")
        subprocess.run([sys.executable, "-m", "pip", "install", "python-magic"], check=True)
        import magic

    # Check if ImageMagick is installed
    stdout, stderr, rc = run_command(["which", "convert"])
    if rc != 0:
        print("WARNING: ImageMagick not found. Some repair methods won't be available.")
        print("Install with: brew install imagemagick")

    # Check if pngcheck is installed
    stdout, stderr, rc = run_command(["which", "pngcheck"])
    if rc != 0:
        print("WARNING: pngcheck not found. PNG analysis won't be available.")
        print("Install with: brew install pngcheck")

    # Run the main analysis
    diagnose_and_fix_images(directory)

    # Create a filtered dataset with only valid images
    create_filtered_dataset(directory, valid_only=True)