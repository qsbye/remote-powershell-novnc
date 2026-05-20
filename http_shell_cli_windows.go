//go:build windows

package main

import (
	"syscall"
	"unsafe"

	"golang.org/x/text/encoding/simplifiedchinese"
	"golang.org/x/text/transform"
)

// enableWindowsVT 启用 Windows 虚拟终端处理（支持 ANSI 颜色）
func enableWindowsVT() {
	kernel32 := syscall.NewLazyDLL("kernel32.dll")
	getConsoleMode := kernel32.NewProc("GetConsoleMode")
	setConsoleMode := kernel32.NewProc("SetConsoleMode")

	handle, err := syscall.GetStdHandle(syscall.STD_OUTPUT_HANDLE)
	if err != nil {
		return
	}
	var mode uint32
	ret, _, _ := getConsoleMode.Call(uintptr(handle), uintptr(unsafe.Pointer(&mode)))
	if ret == 0 {
		return
	}
	mode |= 0x0004 // ENABLE_VIRTUAL_TERMINAL_PROCESSING
	ret, _, _ = setConsoleMode.Call(uintptr(handle), uintptr(mode))
	_ = ret
}

// setHideWindow 设置进程隐藏窗口（Windows 专用）
func setHideWindow(cmd interface{}) {
	// 在 Go 中通过反射设置 SysProcAttr 比较麻烦
	// 这里使用类型断言
	if c, ok := cmd.(interface{ SetSysProcAttr(*syscall.SysProcAttr) }); ok {
		c.SetSysProcAttr(&syscall.SysProcAttr{
			HideWindow: true,
		})
	}
}

// windowsGbkToUTF8 将 GBK 编码转换为 UTF-8
func windowsGbkToUTF8(data []byte) string {
	reader := transform.NewReader(
		&byteReader{data: data},
		simplifiedchinese.GBK.NewDecoder(),
	)
	result := make([]byte, 0, len(data)*2)
	buf := make([]byte, 4096)
	for {
		n, err := reader.Read(buf)
		if n > 0 {
			result = append(result, buf[:n]...)
		}
		if err != nil {
			break
		}
	}
	return string(result)
}

type byteReader struct {
	data []byte
	off  int
}

func (r *byteReader) Read(p []byte) (int, error) {
	if r.off >= len(r.data) {
		return 0, syscall.ERROR_HANDLE_EOF
	}
	n := copy(p, r.data[r.off:])
	r.off += n
	return n, nil
}

// IsWindows 返回 true 表示当前是 Windows 平台
func IsWindows() bool {
	return true
}
