from flask import Flask, render_template, request, send_from_directory, redirect, url_for
from PIL import Image
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['RESULT_FOLDER'] = 'results/'

# Ensure the upload and result directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)

class Steganography:
    BLACK_PIXEL = (0, 0, 0)

    def _int_to_bin(self, rgb):
        """Convert an integer tuple to a binary (string) tuple."""
        r, g, b = rgb
        return f'{r:08b}', f'{g:08b}', f'{b:08b}'

    def _bin_to_int(self, rgb):
        """Convert a binary (string) tuple to an integer tuple."""
        r, g, b = rgb
        return int(r, 2), int(g, 2), int(b, 2)

    def _merge_rgb(self, rgb1, rgb2):
        """Merge two RGB tuples."""
        r1, g1, b1 = self._int_to_bin(rgb1)
        r2, g2, b2 = self._int_to_bin(rgb2)
        rgb = r1[:4] + r2[:4], g1[:4] + g2[:4], b1[:4] + b2[:4]
        return self._bin_to_int(rgb)

    def _unmerge_rgb(self, rgb):
        """Unmerge RGB."""
        r, g, b = self._int_to_bin(rgb)
        new_rgb = r[4:] + '0000', g[4:] + '0000', b[4:] + '0000'
        return self._bin_to_int(new_rgb)

    def merge(self, image1, image2):
        """Merge image2 into image1."""
        if image2.size[0] > image1.size[0] or image2.size[1] > image1.size[1]:
            raise ValueError('Image 2 should be smaller than Image 1!')

        map1 = image1.load()
        map2 = image2.load()

        new_image = Image.new(image1.mode, image1.size)
        new_map = new_image.load()

        for i in range(image1.size[0]):
            for j in range(image1.size[1]):
                is_valid = lambda: i < image2.size[0] and j < image2.size[1]
                rgb1 = map1[i, j]
                rgb2 = map2[i, j] if is_valid() else self.BLACK_PIXEL
                new_map[i, j] = self._merge_rgb(rgb1, rgb2)

        return new_image

    def unmerge(self, image):
        """Unmerge an image."""
        pixel_map = image.load()

        new_image = Image.new(image.mode, image.size)
        new_map = new_image.load()

        for i in range(image.size[0]):
            for j in range(image.size[1]):
                new_map[i, j] = self._unmerge_rgb(pixel_map[i, j])

        return new_image


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image1' not in request.files or 'image2' not in request.files:
        return redirect(request.url)

    image1 = request.files['image1']
    image2 = request.files['image2']

    if image1.filename == '' or image2.filename == '':
        return redirect(request.url)

    # Save uploaded images
    image1_path = os.path.join(app.config['UPLOAD_FOLDER'], 'image1.png')
    image2_path = os.path.join(app.config['UPLOAD_FOLDER'], 'image2.png')
    image1.save(image1_path)
    image2.save(image2_path)

    # Open the images using Pillow
    image1 = Image.open(image1_path)
    image2 = Image.open(image2_path)

    # Perform the merge
    stego = Steganography()
    merged_image = stego.merge(image1, image2)

    # Save merged image
    merged_image_path = os.path.join(app.config['RESULT_FOLDER'], 'merged_image.png')
    merged_image.save(merged_image_path)

    # Return the image URL for frontend to display
    return render_template('index.html', merged_image_url=url_for('uploaded_file', filename='merged_image.png'))


@app.route('/unmerge', methods=['POST'])
def unmerge_image():
    if 'image' not in request.files:
        return redirect(request.url)

    image = request.files['image']

    if image.filename == '':
        return redirect(request.url)

    # Save uploaded image
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'merged_image.png')
    image.save(image_path)

    # Open the image using Pillow
    image = Image.open(image_path)

    # Perform the unmerge
    stego = Steganography()
    unmerged_image = stego.unmerge(image)

    # Save unmerged image
    unmerged_image_path = os.path.join(app.config['RESULT_FOLDER'], 'unmerged_image.png')
    unmerged_image.save(unmerged_image_path)

    # Return the image URL for frontend to display
    return render_template('index.html', unmerged_image_url=url_for('uploaded_file', filename='unmerged_image.png'))


@app.route('/results/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['RESULT_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True)
