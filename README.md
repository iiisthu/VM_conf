这里是用来记录存在的问题和解决方案的

1. 在同一个deployment中添加第二个虚拟机的时候出现错误Conflict。
   原因未知。
   选择不同的host，仍有该错误。
   在不同的deployment创建虚拟机，仍有Conflict错误。
   不同的deployment下，网络设置不同，仍有Conflict错误。
   使用不同的host，仍有Conflict错误。
   原因发现：在同一个service下，如果一个虚拟机正在启动，不能创建新的虚拟机。
   增加对操作返回状态的判断，问题解决！
