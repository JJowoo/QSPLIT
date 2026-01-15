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
        fileContent = utf8.decode(_selectedFile!.bytes!);
      } else if (_selectedFile!.path != null) {
        File file = File(_selectedFile!.path!);
        fileContent = await file.readAsString();
      }

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
    return LayoutBuilder(
      builder: (context, constraints) {
        final isNarrow = constraints.maxWidth < 720;

        Widget fileChip() {
          if (_selectedFile == null) return const SizedBox.shrink();
          return Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: Colors.blue.withAlpha(26),
              borderRadius: BorderRadius.circular(6),
              border: Border.all(color: Colors.blue.withAlpha(77)),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.file_present, color: Colors.blue, size: 14),
                const SizedBox(width: 4),
                Flexible(
                  child: Text(
                    '${_selectedFile!.name} (${(_selectedFile!.size / 1024).toStringAsFixed(1)} KB)',
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                        fontSize: 12, fontWeight: FontWeight.w500),
                  ),
                ),
                const SizedBox(width: 4),
                InkWell(
                  onTap: () {
                    setState(() {
                      _selectedFile = null;
                      _uploadMessage = null;
                    });
                  },
                  child: const Icon(Icons.close, size: 14, color: Colors.grey),
                ),
              ],
            ),
          );
        }

        Widget uploadButton() {
          return ElevatedButton.icon(
            onPressed: _isUploading ? null : _uploadPythonFile,
            icon: _isUploading
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.upload_file),
            label: Text(_isUploading ? 'Uploading...' : 'Upload'),
          );
        }

        Widget targetSection() {
          return Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: Colors.blueGrey.shade800.withAlpha(102),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Target Code:',
                    style: TextStyle(fontWeight: FontWeight.bold)),
                const SizedBox(height: 6),
                Wrap(
                  spacing: 12,
                  runSpacing: 4,
                  children: ['SE', 'PQC', 'MEA'].map((code) {
                    return Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Checkbox(
                          value: widget.selectedTargetCodes.contains(code),
                          onChanged: (val) =>
                              widget.onTargetCodeChanged(code, val ?? false),
                        ),
                        Text(code),
                      ],
                    );
                  }).toList(),
                ),
              ],
            ),
          );
        }

        Widget dummySection() {
          return Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: Colors.blueGrey.shade800.withAlpha(102),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Dummy Code (Auto):',
                    style: TextStyle(fontWeight: FontWeight.bold)),
                const SizedBox(height: 6),
                Wrap(
                  spacing: 12,
                  runSpacing: 4,
                  children: ['SE', 'PQC', 'MEA'].map((code) {
                    final isSelected = widget.selectedDummyCodes.contains(code);
                    return Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Checkbox(
                          value: isSelected,
                          onChanged: null, // 비활성화
                        ),
                        Text(
                          code,
                          style: isSelected
                              ? const TextStyle(
                                  color: Colors.green,
                                  fontWeight: FontWeight.bold,
                                )
                              : const TextStyle(color: Colors.grey),
                        ),
                      ],
                    );
                  }).toList(),
                ),
              ],
            ),
          );
        }

        return Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Colors.white.withAlpha(13),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.grey.shade600),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              isNarrow
                  ? Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Part Selection',
                          style: TextStyle(
                              fontSize: 20, fontWeight: FontWeight.bold),
                        ),
                        if (_selectedFile != null) ...[
                          const SizedBox(height: 8),
                          fileChip(),
                        ],
                        const SizedBox(height: 12),
                        Align(
                          alignment: Alignment.centerRight,
                          child: uploadButton(),
                        ),
                      ],
                    )
                  : Row(
                      children: [
                        const Text(
                          'Part Selection',
                          style: TextStyle(
                              fontSize: 20, fontWeight: FontWeight.bold),
                        ),
                        if (_selectedFile != null) ...[
                          const SizedBox(width: 12),
                          Expanded(child: fileChip()),
                        ],
                        const Spacer(),
                        uploadButton(),
                      ],
                    ),

              if (_uploadMessage != null) ...[
                const SizedBox(height: 10),
                Text(
                  _uploadMessage!,
                  style: TextStyle(
                    color: _messageColor,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],

              const SizedBox(height: 16),

              // Target / Dummy sections
              isNarrow
                  ? Column(
                      children: [
                        targetSection(),
                        const SizedBox(height: 12),
                        dummySection(),
                      ],
                    )
                  : Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(child: targetSection()),
                        const SizedBox(width: 12),
                        Expanded(child: dummySection()),
                      ],
                    ),
            ],
          ),
        );
      },
    );
  }
}
