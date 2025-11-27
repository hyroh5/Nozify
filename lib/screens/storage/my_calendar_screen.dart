// lib/screens/storage/my_calendar_screen.dart
import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../../widgets/topbar/appbar_ver2.dart';
import '../../widgets/bottom_navbar.dart';
import '../home_screen.dart';
import 'package:fl_chart/fl_chart.dart';
import '../../providers/calendar_provider.dart';
import 'package:provider/provider.dart';
import '../../widgets/custom_drawer.dart';

/// ---------------------------
/// 캘린더 전체 페이지
/// ---------------------------
class MyCalendarScreen extends StatefulWidget {
  const MyCalendarScreen({super.key});

  @override
  State<MyCalendarScreen> createState() => _MyCalendarScreenState();
}

class _MyCalendarScreenState extends State<MyCalendarScreen> {
  int _selectedIndex = 3;

  late DateTime _today;
  late DateTime _focusedMonth;
  late DateTime _selectedDay;

  final List<String> _purchasedPerfumes = [
    '블랑쉬 오 드 퍼퓸',
    '필로시코스',
    '잉글리쉬 페어 앤 프리지아',
  ];

  /// 기본 색상 맵 (추가 가능한 mutable)
  final Map<String, Color> _perfumeColors = {
    '블랑쉬 오 드 퍼퓸': const Color(0xFFFFC0C0),
    '필로시코스': const Color(0xFFCBDFA4),
    '잉글리쉬 페어 앤 프리지아': const Color(0xFFC0CEFF),
  };

  final List<String> _situations = ['집', '학교', '데이트', '모임', '업무'];
  final List<String> _weathers = ['맑음', '흐림', '비', '눈'];
  final List<String> _moods = ['설렘', '활기참', '차분함', '편안함', '우울/피곤함'];

  @override
  void initState() {
    super.initState();
    final now = DateTime.now();
    _today = DateTime(now.year, now.month, now.day);
    _focusedMonth = DateTime(now.year, now.month, 1);
    _selectedDay = _today;
  }

  DateTime _dateKey(DateTime d) => DateTime(d.year, d.month, d.day);

  int _daysInMonth(DateTime m) {
    final nextMonth = (m.month == 12)
        ? DateTime(m.year + 1, 1, 1)
        : DateTime(m.year, m.month + 1, 1);
    return nextMonth.subtract(const Duration(days: 1)).day;
  }

  int _startWeekday(DateTime m) {
    final weekday = DateTime(m.year, m.month, 1).weekday; // Mon=1..Sun=7
    return weekday % 7; // Sun=0
  }

  bool _isSameMonth(DateTime a, DateTime b) =>
      a.year == b.year && a.month == b.month;

  /// 미지정 향수 색상 자동 생성(해시 기반 파스텔톤)
  Color _colorForPerfume(String name) {
    try {
      _perfumeColors[name];
    } catch (_) {
      final temp = Map<String, Color>.from(_perfumeColors);
      _perfumeColors.clear();
      _perfumeColors.addAll(temp);
    }

    if (_perfumeColors.containsKey(name)) return _perfumeColors[name]!;

    final rnd = math.Random(name.hashCode);
    final c = Color.fromARGB(
      255,
      170 + rnd.nextInt(70),
      170 + rnd.nextInt(70),
      170 + rnd.nextInt(70),
    );
    _perfumeColors[name] = c;
    return c;
  }

  @override
  Widget build(BuildContext context) {
    final days = _daysInMonth(_focusedMonth);
    final start = _startWeekday(_focusedMonth);
    final totalCells = start + days;
    final rows = (totalCells / 7.0).ceil();

    return Scaffold(
      appBar: const AppBarVer2(),
      endDrawer: const CustomDrawer(),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('향수 캘린더',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),

            // 월 전환
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                IconButton(
                    onPressed: () => setState(() {
                      _focusedMonth = DateTime(
                          _focusedMonth.year, _focusedMonth.month - 1, 1);
                    }),
                    icon: const Icon(Icons.chevron_left)),
                Text('${_focusedMonth.month}월',
                    style: const TextStyle(
                        fontSize: 16, fontWeight: FontWeight.w700)),
                IconButton(
                    onPressed: () => setState(() {
                      _focusedMonth = DateTime(
                          _focusedMonth.year, _focusedMonth.month + 1, 1);
                    }),
                    icon: const Icon(Icons.chevron_right)),
              ],
            ),
            const SizedBox(height: 8),

            // 요일 헤더
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: const [
                _WeekCell('일'),
                _WeekCell('월'),
                _WeekCell('화'),
                _WeekCell('수'),
                _WeekCell('목'),
                _WeekCell('금'),
                _WeekCell('토'),
              ],
            ),
            const SizedBox(height: 8),

            // 날짜 Grid
            Column(
              children: List.generate(rows, (r) {
                return Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: List.generate(7, (c) {
                    final idx = r * 7 + c;
                    if (idx < start || idx >= start + days) {
                      return const _DayCell.empty();
                    }
                    final dayNum = idx - start + 1;
                    final date =
                    DateTime(_focusedMonth.year, _focusedMonth.month, dayNum);
                    final key = _dateKey(date);
                    final monthly = context
                        .watch<CalendarProvider>()
                        .getRecords(date); // 해당 일자 기록
                    final isSelected = _dateKey(_selectedDay) == key;
                    final isToday = _today == key;

                    return _DayCell(
                      day: dayNum,
                      isSelected: isSelected,
                      isToday: isToday,
                      dots: monthly
                          .map((r) => _colorForPerfume(r.perfume))
                          .take(3)
                          .toList(),
                      onTap: () => setState(() => _selectedDay = date),
                    );
                  }),
                );
              }),
            ),

            const SizedBox(height: 16),

            // 선택한 날짜 바
            Row(
              children: [
                Text('${_selectedDay.day}'.padLeft(2, '0'),
                    style: const TextStyle(
                        fontSize: 18, fontWeight: FontWeight.bold)),
                const SizedBox(width: 10),
                if (_selectedDay == _today)
                  const Text('Today',
                      style:
                      TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                const Spacer(),
                // 항상 + 아이콘 유지
                IconButton(
                  icon: const Icon(Icons.add),
                  onPressed: () {
                    _openRecordSheet();
                  },
                ),
              ],
            ),
            const SizedBox(height: 8),

            ..._buildSelectedList(),

            const SizedBox(height: 24),
            const Divider(thickness: 1, color: Color(0xFFE5E5E5)),
            const SizedBox(height: 16),

            const Text('인사이트',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),

            const Text('많이 쓴 향수',
                style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            _buildPie(), // 현재 월 기준

            const SizedBox(height: 20),
            const Text('상황별 패턴',
                style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            _buildStackBars(category: _PatternCategory.situation),

            const SizedBox(height: 20),
            const Text('날씨별 패턴',
                style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            _buildStackBars(category: _PatternCategory.weather),

            const SizedBox(height: 20),
            const Text('기분별 패턴',
                style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            _buildStackBars(category: _PatternCategory.mood),

            const SizedBox(height: 40),
          ],
        ),
      ),
      bottomNavigationBar: BottomNavBar(
        currentIndex: _selectedIndex,
        onTap: (index) {
          setState(() => _selectedIndex = index);
          if (index == 0) {
            Navigator.pushReplacement(
                context, MaterialPageRoute(builder: (_) => const HomeScreen()));
          }
        },
      ),
    );
  }

  /// ---------------------------
  /// 선택일 기록 리스트
  /// ---------------------------
  List<Widget> _buildSelectedList() {
    final calendar = context.watch<CalendarProvider>();
    final list = calendar.getRecords(_selectedDay);
    if (list.isEmpty) {
      return const [
        Padding(
          padding: EdgeInsets.symmetric(vertical: 8, horizontal: 26),
          child: Text('오늘은 아직 향수를 기록하지 않았어요!',
              style: TextStyle(color: Colors.black54)),
        ),
      ];
    }

    return list.asMap().entries.map((entry) {
      final index = entry.key;
      final r = entry.value;

      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 2, horizontal: 6),
        child: Row(
          children: [
            Container(
              width: 8,
              height: 8,
              decoration:
              BoxDecoration(color: _colorForPerfume(r.perfume), shape: BoxShape.circle),
            ),
            const SizedBox(width: 6),
            Expanded(
              child: Text(r.perfume,
                  style: const TextStyle(fontSize: 13, color: Colors.black)),
            ),
            IconButton(
                icon: const Icon(Icons.close, size: 16, color: Colors.black45),
                splashRadius: 16,
                onPressed: () {
                  final calendar = context.read<CalendarProvider>();
                  calendar.removeRecord(_selectedDay, index);
                }),
          ],
        ),
      );
    }).toList();
  }

  /// ---------------------------
  /// 기록 추가 바텀시트 (항상 새로 초기화)
  /// ---------------------------
  void _openRecordSheet() {
    String? selPerfume;
    String? selSituation;
    String? selWeather;
    String? selMood;

    bool isCustomPerfume = false;
    bool isCustomSituation = false;
    bool isCustomWeather = false;
    bool isCustomMood = false;

    final TextEditingController perfumeCtrl = TextEditingController();
    final TextEditingController situationCtrl = TextEditingController();
    final TextEditingController weatherCtrl = TextEditingController();
    final TextEditingController moodCtrl = TextEditingController();

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (_) {
        return Padding(
          padding: EdgeInsets.only(
            left: 16,
            right: 16,
            bottom: MediaQuery.of(context).viewInsets.bottom + 20,
            top: 16,
          ),
          child: StatefulBuilder(
            builder: (context, setBtm) {
              return SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    _dropRow(
                      '오늘 사용한 향수',
                      selPerfume,
                      _purchasedPerfumes,
                          (v) => setBtm(() => selPerfume = v),
                      isCustomPerfume,
                          (val) => setBtm(() => isCustomPerfume = val),
                      perfumeCtrl,
                    ),
                    _dropRow(
                      '사용한 상황',
                      selSituation,
                      _situations,
                          (v) => setBtm(() => selSituation = v),
                      isCustomSituation,
                          (val) => setBtm(() => isCustomSituation = val),
                      situationCtrl,
                    ),
                    _dropRow(
                      '오늘의 날씨',
                      selWeather,
                      _weathers,
                          (v) => setBtm(() => selWeather = v),
                      isCustomWeather,
                          (val) => setBtm(() => isCustomWeather = val),
                      weatherCtrl,
                    ),
                    _dropRow(
                      '오늘의 기분',
                      selMood,
                      _moods,
                          (v) => setBtm(() => selMood = v),
                      isCustomMood,
                          (val) => setBtm(() => isCustomMood = val),
                      moodCtrl,
                    ),
                    const SizedBox(height: 12),
                    SizedBox(
                      width: double.infinity,
                      height: 48,
                      child: ElevatedButton(
                        onPressed: (selPerfume != null &&
                            selSituation != null &&
                            selWeather != null &&
                            selMood != null)
                            ? () {
                          final calendar = context.read<CalendarProvider>();
                          calendar.addRecord(
                            _selectedDay,
                            Record(selPerfume!, selSituation!, selWeather!, selMood!),
                          );
                          Navigator.pop(context);
                        }
                            : null,
                        style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFF384C3B),
                            shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(28))),
                        child: const Text('저장',
                            style: TextStyle(color: Colors.white)),
                      ),
                    ),
                    const SizedBox(height: 8),
                  ],
                ),
              );
            },
          ),
        );
      },
    );
  }

  Widget _dropRow(
      String label,
      String? value,
      List<String> items,
      ValueChanged<String?> onChanged,
      bool isCustom,
      ValueChanged<bool> onCustomChanged,
      TextEditingController customCtrl,
      ) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          DropdownButtonFormField<String>(
            value: isCustom ? '직접 입력' : value,
            items: [
              ...items.map((e) => DropdownMenuItem(value: e, child: Text(e))),
              const DropdownMenuItem(value: '직접 입력', child: Text('직접 입력')),
            ],
            onChanged: (v) {
              if (v == '직접 입력') {
                onCustomChanged(true);
                onChanged(null);
                customCtrl.text = '';
              } else {
                onCustomChanged(false);
                onChanged(v);
              }
            },
            decoration: InputDecoration(
              isDense: true,
              contentPadding:
              const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
              border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: const BorderSide(color: Color(0xFFD8E8D4))),
              focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide:
                  const BorderSide(color: Color(0xFF9FBF99), width: 2)),
              filled: true,
              fillColor: Colors.white,
            ),
            dropdownColor: Colors.white,
          ),
          if (isCustom) ...[
            const SizedBox(height: 10),
            TextField(
              controller: customCtrl,
              decoration: InputDecoration(
                hintText: '직접 입력하세요',
                contentPadding:
                const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              onChanged: (v) => onChanged(v.trim().isEmpty ? null : v.trim()),
            ),
          ],
        ],
      ),
    );
  }

  /// ---------------------------
  /// 인사이트 그래프 (현재 월 기준)
  /// ---------------------------
  Widget _buildPie() {
    final Map<String, int> count = {};
    final calendar = context.watch<CalendarProvider>();

    calendar.records.forEach((key, list) {
      final date = DateTime.parse(key);
      if (!_isSameMonth(date, _focusedMonth)) return;
      for (final r in list) {
        count[r.perfume] = (count[r.perfume] ?? 0) + 1;
      }
    });

    if (count.isEmpty) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: 8),
        child: Text('이 달에는 기록이 아직 없어요',
            style: TextStyle(color: Colors.black54)),
      );
    }

    final total = count.values.fold<int>(0, (a, b) => a + b);
    final entries = count.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));

    return Center(
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          // 왼쪽 라벨
          Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: entries.map((e) {
              final color = _colorForPerfume(e.key);
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 6),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      width: 10,
                      height: 10,
                      decoration:
                      BoxDecoration(color: color, shape: BoxShape.circle),
                    ),
                    const SizedBox(width: 6),
                    Text(e.key, style: const TextStyle(fontSize: 11)),
                  ],
                ),
              );
            }).toList(),
          ),
          const SizedBox(width: 16),
          // 도넛 그래프
          SizedBox(
            width: 200,
            height: 220,
            child: PieChart(
              PieChartData(
                centerSpaceRadius: 20,
                sectionsSpace: 2,
                sections: entries.map((e) {
                  final color = _colorForPerfume(e.key);
                  final pct = (e.value / total) * 100;
                  return PieChartSectionData(
                    color: color,
                    value: e.value.toDouble(),
                    title: '${pct.round()}%',
                    titleStyle: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: Colors.black,
                    ),
                    radius: 70,
                  );
                }).toList(),
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// 패턴 카테고리
  Widget _buildStackBars({required _PatternCategory category}) {
    // 1) 기본 키(사전)
    final baseKeys = switch (category) {
      _PatternCategory.situation => _situations,
      _PatternCategory.weather => _weathers,
      _PatternCategory.mood => _moods,
    };

    // 2) 현재 월 기록에서 등장한 추가 키 수집
    final calendar = context.watch<CalendarProvider>();
    final Set<String> dynamicKeys = {};
    calendar.records.forEach((key, list) {
      final date = DateTime.parse(key);
      if (!_isSameMonth(date, _focusedMonth)) return;
      for (final r in list) {
        switch (category) {
          case _PatternCategory.situation:
            if (r.situation.isNotEmpty && !baseKeys.contains(r.situation)) {
              dynamicKeys.add(r.situation);
            }
            break;
          case _PatternCategory.weather:
            if (r.weather.isNotEmpty && !baseKeys.contains(r.weather)) {
              dynamicKeys.add(r.weather);
            }
            break;
          case _PatternCategory.mood:
            if (r.mood.isNotEmpty && !baseKeys.contains(r.mood)) {
              dynamicKeys.add(r.mood);
            }
            break;
        }
      }
    });

    // 3) 최종 키: 기본키 + 동적키(가나다 순)
    final keys = [
      ...baseKeys,
      ...dynamicKeys.toList()..sort(),
    ];

    const barHeight = 12.0;

    return Column(
      children: keys.map((k) {
        final Map<String, int> cnt = {};
        int sum = 0;

        calendar.records.forEach((key, list) {
          final date = DateTime.parse(key);
          if (!_isSameMonth(date, _focusedMonth)) return;
          for (final r in list) {
            final matches = switch (category) {
              _PatternCategory.situation => r.situation == k,
              _PatternCategory.weather => r.weather == k,
              _PatternCategory.mood => r.mood == k,
            };
            if (matches) {
              cnt[r.perfume] = (cnt[r.perfume] ?? 0) + 1;
              sum++;
            }
          }
        });

        if (sum == 0) {
          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Row(children: [
              SizedBox(width: 48, child: Text(k, textAlign: TextAlign.right)),
              const SizedBox(width: 8),
              const Expanded(
                  child: Text('-', style: TextStyle(color: Colors.grey))),
            ]),
          );
        }

        return Padding(
          padding: const EdgeInsets.symmetric(vertical: 6),
          child: Row(
            children: [
              SizedBox(
                width: 48,
                child: Text(k,
                    style: const TextStyle(fontSize: 12),
                    textAlign: TextAlign.right),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Container(
                  height: barHeight,
                  decoration: const BoxDecoration(
                    border: Border(
                        bottom: BorderSide(color: Colors.black26, width: 1)),
                  ),
                  child: Row(
                    children: cnt.entries.map((e) {
                      final v = e.value / sum;
                      return Expanded(
                        flex: (v * 1000).round(),
                        child: Container(
                          color: _colorForPerfume(e.key),
                        ),
                      );
                    }).toList(),
                  ),
                ),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }
}

enum _PatternCategory { situation, weather, mood }

/// ---------------------------
/// 요일 셀
/// ---------------------------
class _WeekCell extends StatelessWidget {
  const _WeekCell(this.label, {super.key});
  final String label;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 36,
      child: Center(
        child: Text(label, style: const TextStyle(color: Colors.black54)),
      ),
    );
  }
}

/// ---------------------------
/// 날짜 셀
/// ---------------------------
class _DayCell extends StatelessWidget {
  const _DayCell({
    super.key,
    required this.day,
    required this.isSelected,
    required this.isToday,
    required this.dots,
    required this.onTap,
  });

  const _DayCell.empty({super.key})
      : day = 0,
        isSelected = false,
        isToday = false,
        dots = const [],
        onTap = null;

  final int day;
  final bool isSelected;
  final bool isToday;
  final List<Color> dots;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    if (day == 0) return const SizedBox(width: 36, height: 46);
    return InkWell(
      onTap: onTap,
      child: SizedBox(
        width: 36,
        child: Column(
          children: [
            Container(
              width: 28,
              height: 28,
              decoration: BoxDecoration(
                color: isSelected ? Colors.grey.shade300 : Colors.transparent,
                shape: BoxShape.circle,
              ),
              alignment: Alignment.center,
              child: Text(
                '$day',
                style: TextStyle(
                  fontWeight: isToday ? FontWeight.bold : FontWeight.normal,
                ),
              ),
            ),
            const SizedBox(height: 2),
            SizedBox(
              height: 8,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: dots
                    .map((c) => Container(
                  width: 6,
                  height: 6,
                  margin: const EdgeInsets.symmetric(horizontal: 1),
                  decoration: BoxDecoration(
                    color: c,
                    shape: BoxShape.circle,
                  ),
                ))
                    .toList(),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
