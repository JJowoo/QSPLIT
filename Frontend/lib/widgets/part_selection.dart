// part_selection.dart
import 'dart:convert';
import 'dart:io';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

class PartSelection extends StatefulWidget {
  final Set<String> selectedTargetCodes;
  final Set<String> selectedDummyCodes;
  final Function(String, bool) onTargetCodeChanged;
  final Function(String, bool) onDummyCodeChanged;
  final Function(String, String, int)? onUploadPythonFile;

  const PartSelection({
    super.key,
    required this.selectedTargetCodes,
    required this.selectedDummyCodes,
    required this.onTargetCodeChanged,
    required this.onDummyCodeChanged,
    this.onUploadPythonFile,
  });

  @override
  State<PartSelection> createState() => _PartSelectionState();
}

class _PartSelectionState extends State<PartSelection> {
  bool _isUploading = false;
  String? _uploadMessage;
  Color _messageColor = Colors.green;
  PlatformFile? _selectedFile;

  Future<void> _uploadPythonFile() async {
    try {
      // 파일 선택
      FilePickerResult? result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['py'],
        allowMultiple: false,
      );

      if (result != null) {
        setState(() {
          _selectedFile = result.files.first;
        });

        // 파일 업로드
        await _uploadToServer();
      }
    } catch (e) {
      _showMessage('File selection error: $e', Colors.red);
    }
  }

  Future<void> _uploadToServer() async {
    if (_selectedFile == null) {
      _showMessage('No file selected.', Colors.red);
      return;
    }

    setState(() {
      _isUploading = true;
      _uploadMessage = 'Uploading...';
      _messageColor = Colors.blue;
    });

    try {
      // 파일 내용 읽기
      String fileContent = '';
      if (_selectedFile!.bytes != null) {
        // 웹에서 선택된 파일
        fileContent = utf8.decode(_selectedFile!.bytes!);
      } else if (_selectedFile!.path != null) {
        // 데스크톱/모바일에서 선택된 파일
        File file = File(_selectedFile!.path!);
        fileContent = await file.readAsString();
      }

      // home_screen.dart의 upload API 호출
      if (widget.onUploadPythonFile != null) {
        widget.onUploadPythonFile!(
          _selectedFile!.name,
          fileContent,
          _selectedFile!.size,
        );

        setState(() {
          _uploadMessage = 'Upload successful! File: ${_selectedFile!.name}';
          _messageColor = Colors.green;
        });
      } else {
        setState(() {
          _uploadMessage = 'Upload callback not configured.';
          _messageColor = Colors.red;
        });
      }
    } catch (e) {
      setState(() {
        _uploadMessage = 'Upload error: $e';
        _messageColor = Colors.red;
      });
    } finally {
      setState(() {
        _isUploading = false;
      });
    }
  }

  void _showMessage(String message, Color color) {
    setState(() {
      _uploadMessage = message;
      _messageColor = color;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey.shade600),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header with Upload button
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Part Selection',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
              ),
              ElevatedButton.icon(
                onPressed: _isUploading ? null : _uploadPythonFile,
                icon: _isUploading
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.upload_file),
                label: Text(_isUploading ? 'Uploading...' : 'Upload'),
              ),
            ],
          ),

          // Selected file info
          if (_selectedFile != null) ...[
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.blue.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.blue.withOpacity(0.3)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.file_present, color: Colors.blue, size: 16),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Selected file: ${_selectedFile!.name}',
                          style: const TextStyle(fontWeight: FontWeight.bold),
                        ),
                        Text(
                          'Size: ${(_selectedFile!.size / 1024).toStringAsFixed(2)} KB',
                          style:
                              const TextStyle(fontSize: 12, color: Colors.grey),
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    onPressed: () {
                      setState(() {
                        _selectedFile = null;
                        _uploadMessage = null;
                      });
                    },
                    icon: const Icon(Icons.close, size: 16),
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                  ),
                ],
              ),
            ),
          ],

          // Upload message
          if (_uploadMessage != null) ...[
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: _messageColor.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: _messageColor.withOpacity(0.3)),
              ),
              child: Row(
                children: [
                  Icon(
                    _messageColor == Colors.green
                        ? Icons.check_circle
                        : _messageColor == Colors.red
                            ? Icons.error
                            : Icons.info,
                    color: _messageColor,
                    size: 16,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      _uploadMessage!,
                      style: TextStyle(color: _messageColor),
                    ),
                  ),
                ],
              ),
            ),
          ],

          const SizedBox(height: 16),

          // Target and Dummy Code Sections Side by Side
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Target Code
              Expanded(
                child: Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  decoration: BoxDecoration(
                    color: Colors.blueGrey.shade800.withOpacity(0.4),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Target Code:',
                          style: TextStyle(fontWeight: FontWeight.bold)),
                      const SizedBox(height: 6),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.start,
                        children: ['SE', 'PQC', 'MEA'].map((code) {
                          return Row(
                            children: [
                              Checkbox(
                                value:
                                    widget.selectedTargetCodes.contains(code),
                                onChanged: (val) => widget.onTargetCodeChanged(
                                    code, val ?? false),
                              ),
                              Text(code),
                            ],
                          );
                        }).toList(),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 12),

              // Dummy Code (자동 선택 - 읽기 전용)
              Expanded(
                child: Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  decoration: BoxDecoration(
                    color: Colors.blueGrey.shade800.withOpacity(0.4),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Dummy Code (Auto):',
                          style: TextStyle(fontWeight: FontWeight.bold)),
                      const SizedBox(height: 6),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.start,
                        children: ['SE', 'PQC', 'MEA'].map((code) {
                          final isSelected =
                              widget.selectedDummyCodes.contains(code);
                          return Row(
                            children: [
                              Checkbox(
                                value: isSelected,
                                onChanged: null, // 비활성화
                              ),
                              Text(code,
                                  style: isSelected
                                      ? const TextStyle(
                                          color: Colors.green,
                                          fontWeight: FontWeight.bold)
                                      : const TextStyle(color: Colors.grey)),
                            ],
                          );
                        }).toList(),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
