/**
 * Global Image Cropper Module
 * Provides a reusable image cropping interface for the entire application
 * Uses Cropper.js library and Bootstrap 5 modal
 */

const GlobalCropper = (function() {
    // Private variables
    let cropper = null;
    let cropModal = null;
    let resolveCallback = null;
    let rejectCallback = null;
    let scaleX = 1;
    let scaleY = 1;
    let currentFileName = '';
    
    // DOM elements (initialized after DOM loads)
    let modalElement = null;
    let cropperImage = null;
    let aspectRatioButtons = null;
    let rotateLeftBtn = null;
    let rotateRightBtn = null;
    let flipHorizontalBtn = null;
    let flipVerticalBtn = null;
    let resetCropBtn = null;
    let cropAndSaveBtn = null;
    let cancelBtn = null;
    let closeBtn = null;
    
    /**
     * Initialize the cropper module (call after DOM is ready)
     */
    function init() {
        // Get DOM references
        modalElement = document.getElementById('globalCropModal');
        cropperImage = document.getElementById('globalCropperImage');
        aspectRatioButtons = document.querySelectorAll('#globalAspectRatioGroup [data-ratio]');
        rotateLeftBtn = document.getElementById('globalRotateLeft');
        rotateRightBtn = document.getElementById('globalRotateRight');
        flipHorizontalBtn = document.getElementById('globalFlipHorizontal');
        flipVerticalBtn = document.getElementById('globalFlipVertical');
        resetCropBtn = document.getElementById('globalResetCrop');
        cropAndSaveBtn = document.getElementById('globalCropAndSave');
        cancelBtn = document.getElementById('globalCropCancel');
        closeBtn = document.getElementById('globalCropModalClose');
        
        if (!modalElement) {
            console.error('GlobalCropper: Modal element #globalCropModal not found');
            return;
        }
        
        // Initialize Bootstrap modal
        cropModal = new bootstrap.Modal(modalElement, {
            backdrop: 'static',
            keyboard: false
        });
        
        // Set up event listeners
        setupEventListeners();
    }
    
    /**
     * Set up all event listeners
     */
    function setupEventListeners() {
        // Aspect ratio buttons
        aspectRatioButtons.forEach(button => {
            button.addEventListener('click', function() {
                aspectRatioButtons.forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');
                
                const ratio = this.dataset.ratio;
                if (cropper) {
                    if (ratio === 'free') {
                        cropper.setAspectRatio(NaN);
                    } else {
                        cropper.setAspectRatio(parseFloat(ratio));
                    }
                }
            });
        });
        
        // Rotate left
        rotateLeftBtn.addEventListener('click', () => {
            if (cropper) cropper.rotate(-45);
        });
        
        // Rotate right
        rotateRightBtn.addEventListener('click', () => {
            if (cropper) cropper.rotate(45);
        });
        
        // Flip horizontal
        flipHorizontalBtn.addEventListener('click', () => {
            if (cropper) {
                scaleX = -scaleX;
                cropper.scaleX(scaleX);
            }
        });
        
        // Flip vertical
        flipVerticalBtn.addEventListener('click', () => {
            if (cropper) {
                scaleY = -scaleY;
                cropper.scaleY(scaleY);
            }
        });
        
        // Reset crop
        resetCropBtn.addEventListener('click', () => {
            if (cropper) {
                cropper.reset();
                scaleX = 1;
                scaleY = 1;
            }
        });
        
        // Crop and save
        cropAndSaveBtn.addEventListener('click', handleCropAndSave);
        
        // Cancel buttons
        cancelBtn.addEventListener('click', handleCancel);
        closeBtn.addEventListener('click', handleCancel);
        
        // Modal shown event - initialize cropper
        modalElement.addEventListener('shown.bs.modal', initializeCropper);
        
        // Modal hidden event - cleanup
        modalElement.addEventListener('hidden.bs.modal', cleanup);
    }
    
    /**
     * Initialize the cropper instance
     */
    function initializeCropper() {
        if (!cropperImage || !cropperImage.src) return;
        
        // Destroy existing cropper if any
        if (cropper) {
            cropper.destroy();
            cropper = null;
        }
        
        // Create new cropper instance
        cropper = new Cropper(cropperImage, {
            aspectRatio: 1, // Default to square
            viewMode: 2,
            autoCropArea: 0.8,
            responsive: true,
            background: false,
            zoomable: true,
            scalable: true,
            rotatable: true,
            dragMode: 'move',
            cropBoxResizable: true,
            cropBoxMovable: true,
            toggleDragModeOnDblclick: true,
        });
    }
    
    /**
     * Handle crop and save action
     */
    function handleCropAndSave() {
        if (!cropper || !resolveCallback) return;
        
        // Get cropped canvas
        const canvas = cropper.getCroppedCanvas({
            maxWidth: 1200,
            maxHeight: 1200,
            fillColor: '#fff',
            imageSmoothingEnabled: true,
            imageSmoothingQuality: 'high',
        });
        
        // Convert canvas to blob
        canvas.toBlob(function(blob) {
            if (blob) {
                // Create File object from blob
                const croppedFile = new File([blob], currentFileName, {
                    type: blob.type || 'image/jpeg',
                    lastModified: Date.now()
                });
                
                // Resolve promise with File object
                resolveCallback({
                    file: croppedFile,
                    blob: blob,
                    dataURL: canvas.toDataURL('image/jpeg', 0.9),
                    fileName: currentFileName
                });
                
                // Close modal
                cropModal.hide();
            } else {
                console.error('GlobalCropper: Failed to create blob from canvas');
                if (rejectCallback) {
                    rejectCallback(new Error('Failed to create blob from canvas'));
                }
            }
        }, 'image/jpeg', 0.9);
    }
    
    /**
     * Handle cancel action
     */
    function handleCancel() {
        if (rejectCallback) {
            rejectCallback(new Error('User cancelled cropping'));
        }
        cropModal.hide();
    }
    
    /**
     * Cleanup when modal is closed
     */
    function cleanup() {
        if (cropper) {
            cropper.destroy();
            cropper = null;
        }
        
        // Reset scales
        scaleX = 1;
        scaleY = 1;
        
        // Reset aspect ratio buttons
        aspectRatioButtons.forEach(btn => btn.classList.remove('active'));
        const squareBtn = document.querySelector('#globalAspectRatioGroup [data-ratio="1"]');
        if (squareBtn) squareBtn.classList.add('active');
        
        // Clear image
        if (cropperImage) cropperImage.src = '';
        
        // Clear callbacks
        resolveCallback = null;
        rejectCallback = null;
        currentFileName = '';
    }
    
    /**
     * Open the crop modal with an image file
     * @param {File} file - The image file to crop
     * @param {Object} options - Cropping options
     * @param {number} options.aspectRatio - Initial aspect ratio (default: 1 for square)
     * @param {number} options.maxWidth - Maximum output width (default: 1200)
     * @param {number} options.maxHeight - Maximum output height (default: 1200)
     * @returns {Promise} Promise that resolves with cropped image data
     */
    function open(file, options = {}) {
        return new Promise((resolve, reject) => {
            // Validate inputs
            if (!file || !file.type.startsWith('image/')) {
                reject(new Error('Invalid file: must be an image'));
                return;
            }
            
            if (!cropModal) {
                reject(new Error('GlobalCropper not initialized. Call init() first.'));
                return;
            }
            
            // Store callbacks
            resolveCallback = resolve;
            rejectCallback = reject;
            currentFileName = file.name;
            
            // Read file and set image source
            const reader = new FileReader();
            
            reader.onload = function(e) {
                cropperImage.src = e.target.result;
                
                // Set aspect ratio if provided
                const aspectRatio = options.aspectRatio || 1;
                
                // Reset and activate appropriate aspect ratio button
                aspectRatioButtons.forEach(btn => btn.classList.remove('active'));
                
                if (aspectRatio === 'free' || isNaN(aspectRatio)) {
                    const freeBtn = document.querySelector('#globalAspectRatioGroup [data-ratio="free"]');
                    if (freeBtn) freeBtn.classList.add('active');
                } else {
                    // Find closest matching button
                    let closestBtn = null;
                    let closestDiff = Infinity;
                    
                    aspectRatioButtons.forEach(btn => {
                        const ratio = btn.dataset.ratio;
                        if (ratio !== 'free') {
                            const diff = Math.abs(parseFloat(ratio) - aspectRatio);
                            if (diff < closestDiff) {
                                closestDiff = diff;
                                closestBtn = btn;
                            }
                        }
                    });
                    
                    if (closestBtn) closestBtn.classList.add('active');
                }
                
                // Show modal
                cropModal.show();
            };
            
            reader.onerror = function() {
                reject(new Error('Failed to read image file'));
            };
            
            reader.readAsDataURL(file);
        });
    }
    
    /**
     * Close the crop modal
     */
    function close() {
        if (cropModal) {
            cropModal.hide();
        }
    }
    
    // Public API
    return {
        init: init,
        open: open,
        close: close
    };
})();

// Expose to global scope
window.GlobalCropper = GlobalCropper;

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => GlobalCropper.init());
} else {
    GlobalCropper.init();
}
