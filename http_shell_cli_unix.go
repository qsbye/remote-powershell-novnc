//go:build !windows

package main

import (
	"os/exec"
	"syscall"
)

// enableWindowsVT Unix 平台空实现
func enableWindowsVT() {}

// setHideWindow Unix 平台空实现
func setHideWindow(cmd interface{}) {
	if c, ok := cmd.(*exec.Cmd); ok {
		c.SysProcAttr = &syscall.SysProcAttr{}
	}
}

// windowsGbkToUTF8 Unix 平台直接返回原字符串
func windowsGbkToUTF8(data []byte) string {
	return string(data)
}

// IsWindows 返回 false 表示当前不是 Windows 平台
func IsWindows() bool {
	return false
}
