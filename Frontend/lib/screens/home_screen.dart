// home_screen.dart
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:url_launcher/url_launcher.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

import '../widgets/code_layer.dart';
import '../widgets/dummy_generation.dart';
import '../widgets/hyperparameter_config.dart';
import '../widgets/log_panel.dart';
import '../widgets/part_selection.dart';
import '../widgets/results_panel.dart';

class QuantumHomePage extends StatefulWidget {
  const QuantumHomePage({super.key});

  @override
  _QuantumHomePageState createState() => _QuantumHomePageState();
}

class _QuantumHomePageState extends State<QuantumHomePage> {
  Set<String> selectedTargetCodes = {'SE'};
  Set<String> selectedDummyCodes = {'PQC', 'MEA'};
  String selectedLayer = 'StateEncoder';
  int numberOfDummies = 5;
  List<Map<String, dynamic>> dummyData = [];
  final log = <String>['>: Ready.'];
  String selectedDummyCode = ''; // DummyGeneration용 단일 선택 상태
  WebSocketChannel? _logChannel;
  String? _activeRunId;

  final nQubitsController = TextEditingController(text: '6');
  final batchSizeController = TextEditingController(text: '1');
  final depthController = TextEditingController(text: '1');
  final epochsController = TextEditingController(text: '5');
  final optimizerController = TextEditingController(text: 'Adam');
  final lrController = TextEditingController(text: '1e-4');

  Widget _divider() => Divider(color: Colors.grey[700], thickness: 1.0);

  @override
  void dispose() {
    _logChannel?.sink.close();
    super.dispose();
  }

  void connectLogWebSocket() {
    _logChannel?.sink.close(); // 기존 연결 종료
    _logChannel =
        WebSocketChannel.connect(Uri.parse('ws://localhost:8000/ws/logs'));
    _logChannel!.stream.listen((message) {
      Map<String, dynamic>? data;
      try {
        if (message is String) {
          final decoded = jsonDecode(message);
          if (decoded is Map) {
            data = Map<String, dynamic>.from(decoded);
          }
        } else if (message is Map) {
          data = Map<String, dynamic>.from(message);
        }
      } catch (_) {
        data = null;
      }

      // 1) 에포크 끝 이벤트만 반영 (요구사항: 꼭 epoch 단위)
      if (data != null && data['type'] == 'train_epoch_end') {
        final runId = (data['run_id'] ?? '').toString();
        // 다른 run의 이벤트는 무시 (로그/히스토리 mismatch 방지)
        if (_activeRunId != null && runId.isNotEmpty && runId != _activeRunId) {
          return;
        }

        final dummyId = (data['dummy_id'] ?? '').toString();
        final epoch = (data['epoch'] as num?)?.toInt();
        final trainLoss = (data['train_loss'] as num?)?.toDouble();
        final trainAcc = (data['train_acc'] as num?)?.toDouble();

        if (dummyId.isNotEmpty &&
            epoch != null &&
            trainLoss != null &&
            trainAcc != null) {
          setState(() {
            final idx = dummyData
                .indexWhere((e) => e['dummy_id'].toString() == dummyId);
            if (idx != -1) {
              final cur = Map<String, dynamic>.from(dummyData[idx]);
              final rawHistory =
                  (cur['history'] as List<dynamic>?) ?? <dynamic>[];
              final history = rawHistory
                  .map<Map<String, dynamic>>((h) => h is Map
                      ? Map<String, dynamic>.from(h)
                      : <String, dynamic>{})
                  .toList();

              // 같은 epoch가 이미 있으면 업데이트(덮어쓰기), 없으면 append
              final existing = history
                  .indexWhere((h) => (h['epoch'] as num?)?.toInt() == epoch);
              final point = <String, dynamic>{
                'epoch': epoch,
                'train_loss': trainLoss,
                'train_acc': trainAcc,
              };
              if (existing >= 0) {
                history[existing] = point;
              } else {
                history.add(point);
              }

              cur['history'] = history;
              dummyData[idx] = cur;
            }
          });
          return;
        }
      }

      // 2) 일반 message 로그는 기존대로 LogPanel에 표시
      if (data != null && data['message'] is String) {
        final msg = data['message'] as String;
        final runId = (data['run_id'] ?? '').toString();
        if (_activeRunId != null && runId.isNotEmpty && runId != _activeRunId) {
          return;
        }
        String formattedMsg = msg.replaceAll('/home/dev/QSPLIT/softwarex', '..');
        setState(() {
          log.add(formattedMsg);
        });
      } else {
        String formattedMsg = message.toString().replaceAll('/home/dev/QSPLIT/softwarex', '..');
        setState(() {
          log.add(formattedMsg);
        });
      }
    }, onDone: () {
      setState(() {
        log.add('>: WebSocket closed');
      });
    }, onError: (error) {
      setState(() {
        log.add('>: WebSocket error: $error');
      });
    });
  }

  Future<void> generateDummies() async {
    connectLogWebSocket();
    setState(() {
      log.add('>: [Generate] Starting API request...');
    });

    // 기본 파라미터들
    String url =
        'http://localhost:8000/generate-code?n_qubits=${nQubitsController.text}&variant_count=${numberOfDummies.toString()}&depth=${depthController.text}';

    // 각 선택된 Target Code를 개별 파라미터로 추가
    for (final code in selectedTargetCodes) {
      final partName = code == 'SE' ? 'encoder' : code.toLowerCase();
      url += '&target_parts=$partName';
    }

    await _sendApiRequest('/generate-code', url);
  }

  Future<void> runTestWithSavedWeights() async {
    // Run에서도 WS를 연결해야 실시간 epoch_end 이벤트를 받을 수 있음
    connectLogWebSocket();

    final runId = DateTime.now().millisecondsSinceEpoch.toString();
    setState(() {
      _activeRunId = runId;
    });

    setState(() {
      log.add('>: [Run] Starting API request...');
    });

    // IMPORTANT: 기존 dummyData(더미 정보/이미지)를 덮어쓰지 않는다.
    // 대신 history 필드만 보장해서 실시간 epoch_end 업데이트가 들어갈 자리를 만든다.
    setState(() {
      for (var i = 0; i < dummyData.length; i++) {
        final cur = Map<String, dynamic>.from(dummyData[i]);
        cur['history'] =
            (cur['history'] as List<dynamic>?)?.cast<Map<String, dynamic>>() ??
                <Map<String, dynamic>>[];
        dummyData[i] = cur;
      }

      // 만약 아직 더미를 generate 하지 않은 상태면 최소 슬롯만 준비(이미지는 어차피 없음)
      if (dummyData.isEmpty) {
        dummyData = List.generate(numberOfDummies, (i) {
          return <String, dynamic>{
            'dummy_id': (i + 1).toString(),
            'accuracy': 0.0,
            'train_seconds': 0.0,
            'history': <Map<String, dynamic>>[],
            'info': <String, dynamic>{},
          };
        });
      }

      if (selectedDummyCode.isEmpty && dummyData.isNotEmpty) {
        selectedDummyCode = dummyData.first['dummy_id'] as String;
      }
    });

    final queryParams = {
      'target_parts':
          selectedTargetCodes.map((code) => code.toLowerCase()).join(','),
      'n_qubits': nQubitsController.text,
      'variant_counts': '3',
      'sample_count': '5',
      'dummy_codes':
          selectedDummyCodes.map((code) => code.toLowerCase()).join(','),
      'layer': selectedLayer,
      'batch_size': batchSizeController.text,
      'depth': depthController.text,
      'to_device': 'cuda:0',
      'train_epochs': epochsController.text,
      'optimizer': optimizerController.text,
      'lr': lrController.text,
      'variant_count': numberOfDummies.toString(),
      'run_id': runId,
    };

    await _sendApiRequest('/run-multi-test', queryParams);
  }

  Future<void> exportDummyWeights() async {
    setState(() {
      log.add('>: [Export] Starting dummy bundle export...');
    });

    if (selectedDummyCode.isEmpty) {
      setState(() {
        log.add('>: [Export] Error: No dummy code selected for export.');
      });
      return;
    }

    final int? index = int.tryParse(selectedDummyCode);
    if (index == null) {
      setState(() {
        log.add('>: [Export] Error: Invalid dummy code format.');
      });
      return;
    }

    final nQubits = nQubitsController.text;
    final url =
        'http://localhost:8000/download-dummy-all/?n_qubits=$nQubits&include_info=true&allow_partial=true';

    setState(() {
      log.add('>: [Export] Requesting download from: $url');
    });

    try {
      final uri = Uri.parse(url);
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri);
        setState(() {
          log.add('>: [Export] Download initiated successfully.');
        });
      } else {
        setState(() {
          log.add('>: [Export] Could not launch URL: $url');
        });
      }
    } catch (e) {
      setState(() {
        log.add('>: [Export] Error occurred during export: $e');
      });
    }
  }

  // 파일 업로드 테스트를 위한 추가 함수들
  Future<void> testUploadWithSampleFile() async {
    setState(() {
      log.add('>: [Test] Starting sample Python file upload test...');
    });

    // 샘플 파이썬 코드 생성
    const sampleCode = '''
# 샘플 파이썬 파일
class TestClass:
    def __init__(self):
        self.name = "test"
        self.value = 42
    
    def get_info(self):
        return f"Name: {self.name}, Value: {self.value}"

if __name__ == "__main__":
    obj = TestClass()
    print(obj.get_info())
''';

    const filename = 'test_sample.py';
    const content = sampleCode;
    final size = utf8.encode(content).length;

    log.add('>: [Test] Sample file creation completed');
    log.add('>: [Test] Filename: $filename');
    log.add('>: [Test] File size: ${(size / 1024).toStringAsFixed(2)} KB');

    // 파일 업로드 실행
    await uploadPythonFile(filename, content, size);
  }

  Future<void> listUploadedFiles() async {
    setState(() {
      log.add('>: [List] Fetching uploaded file list...');
    });

    try {
      final response = await http.get(
        Uri.parse('http://localhost:8000/api/file/list-files'),
      );

      if (response.statusCode == 200) {
        final responseData = jsonDecode(response.body);
        final files = responseData['files'] as List<dynamic>? ?? [];

        setState(() {
          log.add('>: [List] File list retrieved successfully!');
          log.add('>: [List] Found ${files.length} files total.');

          if (files.isNotEmpty) {
            for (final file in files) {
              final filename = file['filename'] as String;
              final fileSize = file['file_size'] as int;
              final createdTime = DateTime.fromMillisecondsSinceEpoch(
                  (file['created_time'] as double).round() * 1000);

              log.add(
                  '>: [List] $filename (${(fileSize / 1024).toStringAsFixed(2)} KB) - ${createdTime.toString().substring(0, 19)}');
            }
          } else {
            log.add('>: [List] No uploaded files found.');
          }
        });
      } else {
        setState(() {
          log.add(
              '>: [List] Failed to retrieve file list: ${response.statusCode}');
          log.add('>: [List] Error: ${response.body}');
        });
      }
    } catch (e) {
      setState(() {
        log.add('>: [List] Error occurred while retrieving file list: $e');
      });
    }
  }

  Future<void> deleteUploadedFile(String filename) async {
    setState(() {
      log.add('>: [Delete] Starting file deletion: $filename');
    });

    try {
      final response = await http.delete(
        Uri.parse('http://localhost:8000/api/file/delete-file/$filename'),
      );

      if (response.statusCode == 200) {
        final responseData = jsonDecode(response.body);
        setState(() {
          log.add('>: [Delete] File deleted successfully!');
          log.add('>: [Delete] ${responseData['message']}');
        });

        // Refresh file list after deletion
        await listUploadedFiles();
      } else {
        setState(() {
          log.add('>: [Delete] File deletion failed: ${response.statusCode}');
          log.add('>: [Delete] Error: ${response.body}');
        });
      }
    } catch (e) {
      setState(() {
        log.add('>: [Delete] Error occurred during file deletion: $e');
      });
    }
  }

  Future<void> uploadPythonFile(
      String filename, String content, int size) async {
    setState(() {
      log.add('>: [Upload] Starting Python file upload...');
      log.add(
          '>: Filename: $filename, Size: ${(size / 1024).toStringAsFixed(2)} KB');
    });

    if (selectedTargetCodes.isEmpty) {
      setState(() {
        log.add('>: [Upload] Error: No target part selected for upload.');
      });
      return;
    }
    final part = selectedTargetCodes.first.toLowerCase();
    log.add('>: [Upload] Target part: $part');

    try {
      // multipart/form-data 요청 생성
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('http://localhost:8000/upload-code'),
      );

      // 'part' 필드 추가
      request.fields['part'] = part;

      // 파일 내용을 바이트로 변환
      var contentBytes = utf8.encode(content);

      // MultipartFile 생성
      var multipartFile = http.MultipartFile.fromBytes(
        'file', // 백엔드에서 기대하는 필드명
        contentBytes,
        filename: filename,
      );

      // 파일 추가
      request.files.add(multipartFile);

      log.add(
          '>: [Upload] MultipartFile created successfully, sending request...');

      // 요청 전송 및 응답 대기
      var streamedResponse = await request.send();

      // Check response status code
      log.add(
          '>: [Upload] Response status code: ${streamedResponse.statusCode}');

      // Read response body
      var responseBody = await streamedResponse.stream.bytesToString();
      log.add('>: [Upload] Response body: $responseBody');

      // Process based on status code
      if (streamedResponse.statusCode == 200) {
        final responseData = jsonDecode(responseBody);
        setState(() {
          log.add('>: [Upload] Python file upload successful!');
          log.add('>: Part: ${responseData['part']}');
          log.add('>: Saved as: ${responseData['saved_as']}');
          log.add('>: Bytes: ${responseData['bytes']}');
          log.add('>: SHA256: ${responseData['sha256']}');
          log.add('>: Message: ${responseData['message']}');
        });
      } else {
        setState(() {
          log.add('>: [Upload] Upload failed: ${streamedResponse.statusCode}');
          log.add('>: Error content: $responseBody');
        });
      }
    } catch (e) {
      setState(() {
        log.add('>: [Upload] Error occurred during upload: $e');
        log.add('>: Error type: ${e.runtimeType}');
      });
    }
  }

  Future<void> _sendApiRequest(String path, dynamic queryParams) async {
    try {
      Uri uri;
      if (queryParams is String) {
        // URL 문자열인 경우
        uri = Uri.parse(queryParams);
      } else {
        // Map인 경우 (기존 방식)
        final queryParametersAll = <String, List<String>>{};
        queryParams.forEach((key, value) {
          if (queryParametersAll.containsKey(key)) {
            queryParametersAll[key]!.add(value);
          } else {
            queryParametersAll[key] = [value];
          }
        });
        uri = Uri.http('localhost:8000', path, queryParametersAll);
      }

      setState(() {
        log.add('>: Sending GET request to: $uri');
      });

      final response = await http.get(uri);

      if (response.statusCode == 200) {
        final responseData = jsonDecode(response.body);
        setState(() {
          log.add('>: API request successful!');
          // log.add('>: Response: ${response.body}');
          if (path == '/run-multi-test') {
            // results 배열에서 dummy_id별 info 파싱
            final results = responseData['results'] as List<dynamic>?;
            if (results != null) {
              dummyData = results.map<Map<String, dynamic>>((e) {
                final rawInfo = e['info'] ?? {};
                final info = <String, dynamic>{};
                rawInfo.forEach((k, v) {
                  info[k] = v is Map ? Map<String, dynamic>.from(v) : v;
                });

                final rawHistory = e['history'] as List<dynamic>? ?? const [];
                final history = rawHistory.map<Map<String, dynamic>>((h) {
                  if (h is Map) return Map<String, dynamic>.from(h);
                  return <String, dynamic>{};
                }).toList();

                return {
                  'dummy_id': e['dummy_id'].toString(),
                  'accuracy': e['max_train_acc'] ??
                      e['train_acc'] ??
                      e['accuracy'] ??
                      0.0,
                  'train_acc': e['train_acc'],
                  'max_train_acc': e['max_train_acc'],
                  'test_accuracy': e['test_accuracy'] ?? e['accuracy'],
                  'train_seconds': e['train_seconds'] ?? 0.0,
                  'history': history,
                  'info': info,
                };
              }).toList();

              // dummy_id 기준 정렬(표/로그/히스토리 매칭 안정화)
              dummyData.sort((a, b) {
                final ai = int.tryParse(a['dummy_id'].toString()) ?? 0;
                final bi = int.tryParse(b['dummy_id'].toString()) ?? 0;
                return ai.compareTo(bi);
              });
            } else {
              dummyData = [];
            }
          } else if (path == '/generate-code') {
            // generate-code API의 새로운 응답 구조 처리
            final results = responseData['results'] as List<dynamic>?;
            if (results != null) {
              dummyData = results.map<Map<String, dynamic>>((e) {
                final dummyParts =
                    e['dummy_parts'] as Map<String, dynamic>? ?? {};
                final info = <String, dynamic>{};

                // dummy_parts의 각 파트 정보를 info로 변환
                dummyParts.forEach((partKey, partValue) {
                  if (partValue is Map<String, dynamic>) {
                    final partInfo =
                        partValue['info'] as Map<String, dynamic>? ?? {};
                    // encoder를 SE로 변환하여 저장
                    final key = partKey == 'encoder' ? 'se' : partKey;
                    info[key] = partInfo;
                  }
                });

                return {
                  'dummy_id': e['dummy_id'].toString(),
                  'accuracy': 0.0, // generate-code는 accuracy 정보가 없으므로 기본값
                  'info': info,
                };
              }).toList();

              // dummy_id 기준 정렬
              dummyData.sort((a, b) {
                final ai = int.tryParse(a['dummy_id'].toString()) ?? 0;
                final bi = int.tryParse(b['dummy_id'].toString()) ?? 0;
                return ai.compareTo(bi);
              });
            } else {
              dummyData = [];
            }
          }

          if (dummyData.isNotEmpty) {
            selectedDummyCode = dummyData.first['dummy_id'] as String;
          } else {
            selectedDummyCode = '';
          }
        });
      } else {
        setState(() {
          log.add('>: API request failed with status: ${response.statusCode}');
          log.add('>: Error: ${response.body}');
        });
      }
    } catch (e) {
      setState(() {
        log.add('>: An error occurred while sending the request:');
        log.add(e.toString());
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Quantum Split Learning UI')),
      body: LayoutBuilder(
        builder: (context, constraints) {
          if (constraints.maxWidth > 1200) {
            return Row(
              children: [
                Expanded(
                  flex: 3,
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: LayoutBuilder(
                      builder: (context, columnConstraints) {
                        if (columnConstraints.maxHeight < 1000) {
                          return SingleChildScrollView(
                            child: Column(
                              children: [
                                PartSelection(
                                  selectedTargetCodes: selectedTargetCodes,
                                  selectedDummyCodes: selectedDummyCodes,
                                  onTargetCodeChanged: (code, val) =>
                                      setState(() {
                                    if (val) {
                                      selectedTargetCodes.add(code);
                                    } else {
                                      selectedTargetCodes.remove(code);
                                    }
                                    selectedDummyCodes.clear();
                                    final allCodes = {'SE', 'PQC', 'MEA'};
                                    for (final code in allCodes) {
                                      if (!selectedTargetCodes.contains(code)) {
                                        selectedDummyCodes.add(code);
                                      }
                                    }
                                  }),
                                  onDummyCodeChanged: (code, val) {},
                                  onUploadPythonFile: uploadPythonFile,
                                ),
                                const SizedBox(height: 20),
                                _divider(),
                                Row(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Expanded(
                                      flex: 1,
                                      child: CodeLayer(
                                        selectedLayer: selectedLayer,
                                        onChanged: (val) =>
                                            setState(() => selectedLayer = val),
                                      ),
                                    ),
                                    const SizedBox(width: 8),
                                    Expanded(
                                      flex: 2,
                                      child: HyperparameterConfig(
                                        nQubitsController: nQubitsController,
                                        batchSizeController:
                                            batchSizeController,
                                        depthController: depthController,
                                        epochsController: epochsController,
                                        optimizerController:
                                            optimizerController,
                                        lrController: lrController,
                                        numberOfDummies: numberOfDummies,
                                        onNumberChanged: (val) => setState(
                                            () => numberOfDummies = val),
                                        onGeneratePressed: generateDummies,
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 20),
                                _divider(),
                                SizedBox(
                                  height: 600,
                                  child: DummyGeneration(
                                    dummyList: dummyData
                                        .map((e) => e['dummy_id'] as String)
                                        .toList(),
                                    dummyData: dummyData,
                                    selectedDummyCode:
                                        selectedDummyCode.isNotEmpty &&
                                                dummyData.any((e) =>
                                                    e['dummy_id'] ==
                                                    selectedDummyCode)
                                            ? selectedDummyCode
                                            : (dummyData.isNotEmpty
                                                ? dummyData.first['dummy_id']
                                                    as String
                                                : ''),
                                    selectedDummyCodes: selectedDummyCodes,
                                    onDummyCodeChanged: (code) => setState(() {
                                      selectedDummyCode = code;
                                    }),
                                    onRunPressed: runTestWithSavedWeights,
                                  ),
                                ),
                              ],
                            ),
                          );
                        } else {
                          return Column(
                            children: [
                              PartSelection(
                                selectedTargetCodes: selectedTargetCodes,
                                selectedDummyCodes: selectedDummyCodes,
                                onTargetCodeChanged: (code, val) =>
                                    setState(() {
                                  if (val) {
                                    selectedTargetCodes.add(code);
                                  } else {
                                    selectedTargetCodes.remove(code);
                                  }
                                  selectedDummyCodes.clear();
                                  final allCodes = {'SE', 'PQC', 'MEA'};
                                  for (final code in allCodes) {
                                    if (!selectedTargetCodes.contains(code)) {
                                      selectedDummyCodes.add(code);
                                    }
                                  }
                                }),
                                onDummyCodeChanged: (code, val) {},
                                onUploadPythonFile: uploadPythonFile,
                              ),
                              const SizedBox(height: 20),
                              _divider(),
                              Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Expanded(
                                    flex: 1,
                                    child: CodeLayer(
                                      selectedLayer: selectedLayer,
                                      onChanged: (val) =>
                                          setState(() => selectedLayer = val),
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    flex: 2,
                                    child: HyperparameterConfig(
                                      nQubitsController: nQubitsController,
                                      batchSizeController: batchSizeController,
                                      depthController: depthController,
                                      epochsController: epochsController,
                                      optimizerController: optimizerController,
                                      lrController: lrController,
                                      numberOfDummies: numberOfDummies,
                                      onNumberChanged: (val) =>
                                          setState(() => numberOfDummies = val),
                                      onGeneratePressed: generateDummies,
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 20),
                              _divider(),
                              Expanded(
                                child: DummyGeneration(
                                  dummyList: dummyData
                                      .map((e) => e['dummy_id'] as String)
                                      .toList(),
                                  dummyData: dummyData,
                                  selectedDummyCode: selectedDummyCode
                                              .isNotEmpty &&
                                          dummyData.any((e) =>
                                              e['dummy_id'] ==
                                              selectedDummyCode)
                                      ? selectedDummyCode
                                      : (dummyData.isNotEmpty
                                          ? dummyData.first['dummy_id']
                                              as String
                                          : ''),
                                  selectedDummyCodes: selectedDummyCodes,
                                  onDummyCodeChanged: (code) => setState(() {
                                    selectedDummyCode = code;
                                  }),
                                  onRunPressed: runTestWithSavedWeights,
                                ),
                              ),
                            ],
                          );
                        }
                      },
                    ),
                  ),
                ),
                Expanded(
                  flex: 2,
                  child: Padding(
                    padding: const EdgeInsets.all(12.0),
                    child: Column(
                      // mainAxisAlignment: MainAxisAlignment.center,
                      // crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        Expanded(child: LogPanel(log: log)),
                        const SizedBox(height: 20),
                        _divider(),
                        Expanded(
                            child: ResultsPanel(
                                dummyData: dummyData,
                                onExport: exportDummyWeights)),
                      ],
                    ),
                  ),
                )
              ],
            );
          } else {
            return SingleChildScrollView(
              padding: const EdgeInsets.all(12),
              child: Column(
                children: [
                  PartSelection(
                    selectedTargetCodes: selectedTargetCodes,
                    selectedDummyCodes: selectedDummyCodes,
                    onTargetCodeChanged: (code, val) => setState(() {
                      if (val) {
                        selectedTargetCodes.add(code);
                      } else {
                        selectedTargetCodes.remove(code);
                      }
                      selectedDummyCodes.clear();
                      final allCodes = {'SE', 'PQC', 'MEA'};
                      for (final code in allCodes) {
                        if (!selectedTargetCodes.contains(code)) {
                          selectedDummyCodes.add(code);
                        }
                      }
                    }),
                    onDummyCodeChanged: (code, val) {},
                    onUploadPythonFile: uploadPythonFile,
                  ),
                  const SizedBox(height: 20),
                  _divider(),
                  constraints.maxWidth > 800
                      ? Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Expanded(
                              flex: 1,
                              child: CodeLayer(
                                selectedLayer: selectedLayer,
                                onChanged: (val) =>
                                    setState(() => selectedLayer = val),
                              ),
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              flex: 2,
                              child: HyperparameterConfig(
                                nQubitsController: nQubitsController,
                                batchSizeController: batchSizeController,
                                depthController: depthController,
                                epochsController: epochsController,
                                optimizerController: optimizerController,
                                lrController: lrController,
                                numberOfDummies: numberOfDummies,
                                onNumberChanged: (val) =>
                                    setState(() => numberOfDummies = val),
                                onGeneratePressed: generateDummies,
                              ),
                            ),
                          ],
                        )
                      : Column(
                          children: [
                            CodeLayer(
                              selectedLayer: selectedLayer,
                              onChanged: (val) =>
                                  setState(() => selectedLayer = val),
                            ),
                            const SizedBox(height: 8),
                            HyperparameterConfig(
                              nQubitsController: nQubitsController,
                              batchSizeController: batchSizeController,
                              depthController: depthController,
                              epochsController: epochsController,
                              optimizerController: optimizerController,
                              lrController: lrController,
                              numberOfDummies: numberOfDummies,
                              onNumberChanged: (val) =>
                                  setState(() => numberOfDummies = val),
                              onGeneratePressed: generateDummies,
                            ),
                          ],
                        ),
                  const SizedBox(height: 20),
                  _divider(),
                  SizedBox(
                    height: 800,
                    child: DummyGeneration(
                      dummyList: dummyData
                          .map((e) => e['dummy_id'] as String)
                          .toList(),
                      dummyData: dummyData,
                      selectedDummyCode: selectedDummyCode.isNotEmpty &&
                              dummyData.any(
                                  (e) => e['dummy_id'] == selectedDummyCode)
                          ? selectedDummyCode
                          : (dummyData.isNotEmpty
                              ? dummyData.first['dummy_id'] as String
                              : ''),
                      selectedDummyCodes: selectedDummyCodes,
                      onDummyCodeChanged: (code) => setState(() {
                        selectedDummyCode = code;
                      }),
                      onRunPressed: runTestWithSavedWeights,
                    ),
                  ),
                  const SizedBox(height: 20),
                  _divider(),
                  SizedBox(
                    height: 300,
                    child: LogPanel(log: log),
                  ),
                  const SizedBox(height: 20),
                  _divider(),
                  SizedBox(
                    height: 300,
                    child: ResultsPanel(
                        dummyData: dummyData, onExport: exportDummyWeights),
                  ),
                ],
              ),
            );
          }
        },
      ),
    );
  }
}
