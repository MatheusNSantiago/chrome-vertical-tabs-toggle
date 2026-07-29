using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Runtime.Serialization;
using System.Runtime.Serialization.Json;
using System.Threading;
using System.Windows.Automation;

internal static class Program
{
    private const string ToggleCommand = "toggle";
    private const string CollapseCommand = "collapse";
    private const string VerticalTabStripClass = "VerticalTabStripRegionView";
    private const int SupportedLabelsSchema = 1;
    private const int StateChangeTimeoutMilliseconds = 1500;

    [MTAThread]
    private static void Main()
    {
        try
        {
            var request = ReadMessage<Request>(Console.OpenStandardInput());
            var state = ControlSidebar(request.Command);
            WriteMessage(Console.OpenStandardOutput(), Response.Success(state));
        }
        catch (Exception error)
        {
            WriteMessage(Console.OpenStandardOutput(), Response.Failure(error.Message));
        }
    }

    private static string ControlSidebar(string command)
    {
        if (command != ToggleCommand && command != CollapseCommand)
        {
            throw new InvalidDataException("unsupported command");
        }

        var labels = ReadLabels();
        if (command == ToggleCommand)
        {
            return ToggleActiveSidebar(labels);
        }
        return CollapseSidebars(labels);
    }

    private static string ToggleActiveSidebar(Labels labels)
    {
        var window = AutomationElement.FromHandle(FindActiveChromeWindowHandle());
        var sidebar = FindVerticalTabStrip(window);
        var button = FindSidebarButton(sidebar, labels);
        var expectedState = CurrentState(button, labels) == "expanded"
            ? "collapsed"
            : "expanded";
        InvokeSidebarButton(button);
        return WaitForState(sidebar, labels, expectedState);
    }

    private static string CollapseSidebars(Labels labels)
    {
        var sidebars = FindChromeWindowHandles()
            .Select(AutomationElement.FromHandle)
            .Select(FindVerticalTabStripOrNull)
            .Where(sidebar => sidebar != null)
            .ToArray();
        if (sidebars.Length == 0)
        {
            throw new InvalidOperationException("Chrome vertical tab strip was not found");
        }

        foreach (var sidebar in sidebars)
        {
            var button = FindSidebarButton(sidebar, labels);
            if (CurrentState(button, labels) == "collapsed")
            {
                continue;
            }
            InvokeSidebarButton(button);
            WaitForState(sidebar, labels, "collapsed");
        }
        return "collapsed";
    }

    private static string CurrentState(AutomationElement button, Labels labels)
    {
        return labels.Expand.Contains(button.Current.Name, StringComparer.Ordinal)
            ? "collapsed"
            : "expanded";
    }

    private static string WaitForState(
        AutomationElement sidebar,
        Labels labels,
        string expectedState
    )
    {
        var elapsed = Stopwatch.StartNew();
        while (elapsed.ElapsedMilliseconds < StateChangeTimeoutMilliseconds)
        {
            var button = FindSidebarButton(sidebar, labels);
            if (CurrentState(button, labels) == expectedState)
            {
                return expectedState;
            }
            Thread.Sleep(50);
        }
        throw new TimeoutException("Chrome did not change the vertical tab sidebar state");
    }

    private static void InvokeSidebarButton(AutomationElement button)
    {
        object pattern;
        if (!button.TryGetCurrentPattern(InvokePattern.Pattern, out pattern))
        {
            throw new InvalidOperationException("Chrome vertical tab toggle has no invoke action");
        }

        ((InvokePattern)pattern).Invoke();
    }

    private static Labels ReadLabels()
    {
        var path = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "sidebar-labels.json");
        using (var input = File.OpenRead(path))
        {
            var labels = (Labels)new DataContractJsonSerializer(typeof(Labels)).ReadObject(input);
            if (labels.SchemaVersion != SupportedLabelsSchema)
            {
                throw new InvalidDataException("unsupported sidebar labels");
            }
            return labels;
        }
    }

    private static AutomationElement FindVerticalTabStrip(AutomationElement window)
    {
        var sidebar = FindVerticalTabStripOrNull(window);
        if (sidebar == null)
        {
            throw new InvalidOperationException("Chrome vertical tab strip was not found");
        }
        return sidebar;
    }

    private static AutomationElement FindVerticalTabStripOrNull(AutomationElement window)
    {
        var condition = new PropertyCondition(
            AutomationElement.ClassNameProperty,
            VerticalTabStripClass
        );
        return window.FindFirst(TreeScope.Descendants, condition);
    }

    private static AutomationElement FindSidebarButton(
        AutomationElement sidebar,
        Labels labels
    )
    {
        var knownLabels = new HashSet<string>(
            labels.Collapse.Concat(labels.Expand),
            StringComparer.Ordinal
        );
        var buttons = sidebar.FindAll(
            TreeScope.Descendants,
            new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Button)
        );
        foreach (AutomationElement button in buttons)
        {
            if (knownLabels.Contains(button.Current.Name))
            {
                return button;
            }
        }
        throw new InvalidOperationException("Chrome vertical tab toggle was not found");
    }

    private static IntPtr FindActiveChromeWindowHandle()
    {
        var foreground = NativeMethods.GetForegroundWindow();
        if (foreground == IntPtr.Zero || !IsChromeWindow(foreground))
        {
            throw new InvalidOperationException("active Chrome or Chromium window was not found");
        }
        return foreground;
    }

    private static IReadOnlyList<IntPtr> FindChromeWindowHandles()
    {
        var windows = new List<IntPtr>();
        NativeMethods.EnumWindows(
            delegate(IntPtr window, IntPtr parameter)
            {
                if (NativeMethods.IsWindowVisible(window) && IsChromeWindow(window))
                {
                    windows.Add(window);
                }
                return true;
            },
            IntPtr.Zero
        );
        return windows;
    }

    private static bool IsChromeWindow(IntPtr window)
    {
        uint processId;
        NativeMethods.GetWindowThreadProcessId(window, out processId);
        using (var process = Process.GetProcessById(unchecked((int)processId)))
        {
            return process.ProcessName.Equals("chrome", StringComparison.OrdinalIgnoreCase);
        }
    }

    private static T ReadMessage<T>(Stream input)
    {
        var header = ReadExactly(input, 4);
        var payload = ReadExactly(input, BitConverter.ToInt32(header, 0));
        using (var message = new MemoryStream(payload))
        {
            return (T)new DataContractJsonSerializer(typeof(T)).ReadObject(message);
        }
    }

    private static byte[] ReadExactly(Stream input, int length)
    {
        var bytes = new byte[length];
        var offset = 0;
        while (offset < length)
        {
            var bytesRead = input.Read(bytes, offset, length - offset);
            if (bytesRead == 0)
            {
                throw new EndOfStreamException("invalid Native Messaging request");
            }
            offset += bytesRead;
        }
        return bytes;
    }

    private static void WriteMessage<T>(Stream output, T response)
    {
        byte[] payload;
        using (var message = new MemoryStream())
        {
            new DataContractJsonSerializer(typeof(T)).WriteObject(message, response);
            payload = message.ToArray();
        }
        var header = BitConverter.GetBytes(payload.Length);
        output.Write(header, 0, header.Length);
        output.Write(payload, 0, payload.Length);
        output.Flush();
    }
}

[DataContract]
internal sealed class Request
{
    [DataMember(Name = "command")]
    public string Command { get; set; }
}

[DataContract]
internal sealed class Response
{
    [DataMember(Name = "state", EmitDefaultValue = false)]
    public string State { get; private set; }

    [DataMember(Name = "error", EmitDefaultValue = false)]
    public string Error { get; private set; }

    public static Response Success(string state)
    {
        return new Response { State = state };
    }

    public static Response Failure(string error)
    {
        return new Response { Error = error };
    }
}

[DataContract]
internal sealed class Labels
{
    [DataMember(Name = "schema_version")]
    public int SchemaVersion { get; set; }

    [DataMember(Name = "collapse")]
    public string[] Collapse { get; set; }

    [DataMember(Name = "expand")]
    public string[] Expand { get; set; }
}

internal static class NativeMethods
{
    internal delegate bool EnumWindowsCallback(IntPtr window, IntPtr parameter);

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    internal static extern bool EnumWindows(
        EnumWindowsCallback callback,
        IntPtr parameter
    );

    [DllImport("user32.dll")]
    internal static extern IntPtr GetForegroundWindow();

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    internal static extern bool IsWindowVisible(IntPtr window);

    [DllImport("user32.dll")]
    internal static extern uint GetWindowThreadProcessId(IntPtr window, out uint processId);
}
