# Bộ dữ liệu kiểm thử độ đúng Sudoku

`manifest.json` liệt kê từng file puzzle, kích thước, kết quả mong đợi và nhóm
chạy. Các file trong `puzzles/` là mảng JSON có thể đưa trực tiếp cho `main.py`.
Với trường hợp SAT, `solutions/` chứa một nghiệm mẫu tương ứng.

## Nguồn và cách tạo

Toàn bộ puzzle trong thư mục này được **tự tạo cho dự án**, không sao chép từ
nguồn bên ngoài. Script `generate.py` lưu công thức và các seed để tái tạo:

- Với N = k², tạo bảng hoàn chỉnh bằng
  `grid[r][c] = (r*k + r//k + c + shift) % N + 1`.
- Xóa số ô ghi trong manifest, dùng `random.Random(seed).sample` với seed cố
  định. Nghiệm ban đầu được lưu làm minh chứng tồn tại nghiệm; việc xóa ô
  **không chứng minh tính duy nhất**. Trường hợp 4x4 rỗng có nhiều nghiệm.
- Các trường hợp UNSAT được tự xây dựng. Ba trường hợp có clue mâu thuẫn
  trực tiếp trong hàng, cột hoặc khối. Trường hợp `04_unsat_no_duplicate`
  không có clue lặp trực tiếp; kiểm thử liệt kê độc lập toàn bộ 288 nghiệm
  Sudoku 4x4 và xác nhận không nghiệm nào phù hợp.
- Các file `invalid_*` cố tình sai định dạng hoặc miền giá trị và phải gây
  `ValueError`. Chúng không phải puzzle UNSAT.

Puzzle mẫu `data/puzzle.json` đã có sẵn trong dự án trước khi tạo bộ này;
nguồn gốc ban đầu của nó chưa được xác minh, nên không gán tác giả hay nguồn.

Các bảng SAT tự sinh đều dựa trên cùng một họ mẫu và có cấu trúc khá đều. Đây
là dữ liệu kiểm tra độ đúng, **không phải** bộ benchmark đại diện cho độ khó
hoặc hiệu năng của solver, nhất là mẫu 100x100 chỉ có một ô trống.

## Chạy kiểm thử

Từ thư mục gốc dự án, sau khi cài `python-sat` vào `.venv`:

```powershell
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Lệnh mặc định chạy các trường hợp tới 25x25 với cả SAT và CP-SAT (nếu đã cài
thư viện tương ứng). Để chạy thêm 36x36 và 49x49:

Gurobi dùng license riêng nên chỉ được chạy trong bộ kiểm thử khi đặt
`$env:SUDOKU_RUN_GUROBI = '1'`. Có thể kết hợp biến này với
`SUDOKU_RUN_LARGE` để kiểm tra 36x36 và 49x49.

```powershell
$env:SUDOKU_RUN_LARGE = '1'
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
Remove-Item Env:SUDOKU_RUN_LARGE
```

100x100 là kiểm tra tự chọn có thể tốn nhiều thời gian và RAM; chỉ chạy khi
máy đủ tài nguyên:

```powershell
$env:SUDOKU_RUN_STRESS = '1'
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
Remove-Item Env:SUDOKU_RUN_STRESS
```

Tái tạo các file do script quản lý bằng
`& .\.venv\Scripts\python.exe data/test_puzzles/generate.py`. Lệnh này ghi đè
các file fixture cùng tên và `manifest.json`.
