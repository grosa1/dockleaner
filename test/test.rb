THIS_DIR = File.dirname(File.absolute_path(__FILE__))
PATH_TO_DOCKLEANER = THIS_DIR + "/../dockleaner.py" 

def dockleaner(path, smell)
    `python #{PATH_TO_DOCKLEANER} -p "#{path}" -d "2023-01-01" --rule "#{smell}" >/dev/null 2>&1`
end

def hadolint(path)
    hadolint_result = `hadolint --no-color "#{path}"`.split("\n")
    smells = hadolint_result.map { |l| l.sub(path, "").split(" ")[1] }.uniq
    return smells
end

Dir.chdir(THIS_DIR) do
    Dir.glob("**/*-fixed").each do |fixed|
        `rm "#{fixed}"`
    end
    
    Dir.glob("**/*-log.html").each do |log|
        `rm "#{log}"`
    end

    to_test = ARGV[0]
    if !to_test.nil?
        puts "Testing smell: #{to_test}"
    else
        puts "Testing smell: ALL"
    end

    Dir.glob("*").select { |f| FileTest.directory?(f) && !%w(. ..).include?(f) }.each do |folder|
        smell = File.basename(folder)
          if !to_test.nil? && !smell.include?(to_test)
              next
          end
        
        Dir.glob(folder + "/*").select { |f| !f.include?("-fixed") && !f.include?("-log.html") }.each do |dockerfile|
            unless hadolint(dockerfile).include?(smell)
                puts "#{dockerfile} is a bad test case: it does not contain #{smell}"
                next
            end
            
            print "Running dockleaner on #{dockerfile}... "
            dockleaner(dockerfile, smell)
            fixed_path = dockerfile + "-fixed"
            if hadolint(fixed_path).include?(smell)
                puts "NOT FIXED!"
            else
                puts "OK"
            end
        end
    end
end
